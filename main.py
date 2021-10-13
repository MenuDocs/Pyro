import io
import os
import re
import logging
import textwrap
import contextlib
from traceback import format_exception

import discord
import motor.motor_asyncio
from discord.ext import commands

from utils import exceptions
from utils.mongo import Document
from utils.util import clean_code
from utils.util import Pag

mongo_url = os.getenv("MONGO")
token = os.getenv("TOKEN")


async def get_prefix(bot, message):
    try:
        data = await bot.config.find(message.guild.id)

        # Make sure we have a use able prefix
        if not data or "prefix" not in data:
            prefix = bot.DEFAULTPREFIX
        else:
            prefix = data["prefix"]
    except exceptions.IdNotFound:
        # No set guild
        prefix = bot.DEFAULTPREFIX
    except AttributeError:
        # Dm's?
        prefix = bot.DEFAULTPREFIX

    if message.content.casefold().startswith(prefix.casefold()):
        # The prefix matches, now return the one the user used
        # such that dpy will dispatch the given command
        prefix_length = len(prefix)
        prefix = message.content[:prefix_length]

    return commands.when_mentioned_or(prefix)(bot, message)


logging.basicConfig(
    format="%(levelname)s | %(asctime)s | %(module)s | %(message)s",
    datefmt="%d/%m/%Y %I:%M:%S %p",
    level=logging.INFO,
)

intents = discord.Intents.none()
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.members = True
intents.emojis = True

bot = commands.Bot(
    command_prefix=get_prefix,
    case_insensitive=True,
    description="A short sharp bot coded in python to aid the python "
    "developers with helping the community "
    "with discord.py related issues.",
    intents=intents,
    help_command=None,
)

logger = logging.getLogger(__name__)

# Use regex to parse mentions, much better than only supporting
# nickname mentions (<@!1234>)
# This basically ONLY matches a string that only consists of a mention
mention = re.compile(r"^<@!?(?P<id>\d+)>$")

bot.DEFAULTPREFIX = "py."


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="py.help"))

    logger.info("I'm all up and ready like mom's spaghetti")

    try:
        await bot.config.get_all()
    except exceptions.PyMongoError as e:
        logger.error("An error occurred while fetching the config: %s" % e)
    else:
        logger.info("Database connection established successfully")


@bot.event
async def on_message(message):
    # Ignore messages sent by bots
    if message.author.bot:
        return

    if message.guild:
        try:
            guild_config = await bot.config.find(message.guild.id)
            if message.channel.id in guild_config["ignored_channels"]:
                return
        except exceptions.IdNotFound:
            pass
        except KeyError:
            pass

    # Whenever the bot is tagged, respond with its prefix
    if match := mention.match(message.content):
        if int(match.group("id")) == bot.user.id:
            data = await bot.config._Document__get_raw(message.guild.id)
            if not data or "prefix" not in data:
                prefix = bot.DEFAULTPREFIX
            else:
                prefix = data["prefix"]

            await message.channel.send(f"My prefix here is `{prefix}`", delete_after=15)

    await bot.process_commands(message)


@bot.command(description="Log the bot out.")
@commands.is_owner()
async def logout(ctx):
    await ctx.send("Cya :wave:")
    await bot.logout()


@bot.command(name="eval", aliases=["exec"])
@commands.is_owner()
async def _eval(ctx, *, code):
    """
    Evaluates given code.
    """
    code = clean_code(code)

    local_variables = {
        "discord": discord,
        "commands": commands,
        "bot": bot,
        "ctx": ctx,
        "channel": ctx.channel,
        "author": ctx.author,
        "guild": ctx.guild,
        "message": ctx.message,
    }

    stdout = io.StringIO()

    try:
        with contextlib.redirect_stdout(stdout):
            exec(
                f"async def func():\n{textwrap.indent(code, '    ')}",
                local_variables,
            )

            obj = await local_variables["func"]()
            result = f"{stdout.getvalue()}\n-- {obj}\n"

    except Exception as e:
        result = "".join(format_exception(e, e, e.__traceback__))

    pager = Pag(
        timeout=180,
        use_defaults=True,
        entries=[result[i : i + 2000] for i in range(0, len(result), 2000)],
        length=1,
        prefix="```py\n",
        suffix="```",
    )

    await pager.start(ctx)


@bot.command()
@commands.is_owner()
async def dbbackup(ctx):
    """Back up the database"""
    await ctx.send("https://giphy.com/gifs/christmas-3P0oEX5oTmrkY")

    backup_db = motor.motor_asyncio.AsyncIOMotorClient(mongo_url).backup
    backup_config = Document(backup_db, "config")
    backup_keywords = Document(backup_db, "keywords")
    backup_quiz = Document(backup_db, "quiz")
    backup_code = Document(backup_db, "code")
    backup_quiz_answers = Document(backup_db, "quizAnswers")
    backup_starboard = Document(backup_db, "starboard")

    for item in await bot.config.get_all():
        await backup_config.upsert(item)

    for item in await bot.keywords.get_all():
        await backup_keywords.upsert(item)

    for item in await bot.quiz.get_all():
        await backup_quiz.upsert(item)

    for item in await bot.code.get_all():
        await backup_code.upsert(item)

    for item in await bot.quiz_answers.get_all():
        await backup_quiz_answers.upsert(item)

    for item in await bot.starboard.get_all():
        await backup_starboard.upsert(item)

    await ctx.send(
        "https://giphy.com/gifs/deliverance-vN3fMMSAmVwoo\n\n*Database backup complete*"
    )


# Load all extensions
if __name__ == "__main__":
    # Database initialization
    bot.db = motor.motor_asyncio.AsyncIOMotorClient(mongo_url).pyro

    bot.config = Document(bot.db, "config")
    bot.keywords = Document(bot.db, "keywords")
    bot.quiz = Document(bot.db, "quiz")
    bot.code = Document(bot.db, "code")
    bot.quiz_answers = Document(bot.db, "quizAnswers")
    bot.starboard = Document(bot.db, "starboard")
    bot.tictactoe = Document(bot.db, "tictactoe")

    for ext in os.listdir("./cogs/"):
        if ext.endswith(".py") and not ext.startswith("_"):
            try:
                bot.load_extension(f"cogs.{ext[:-3]}")
            except Exception as e:
                logger.error(
                    "An error occurred while loading ext cogs.{}: {}".format(
                        ext[:-3], e
                    )
                )

    bot.run(token)
