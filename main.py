import io
import os
import re
import json
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

with open("config.json", "r") as f:
    config = json.load(f)


async def get_prefix(bot, message):
    # If private messages
    if not message.guild:
        return commands.when_mentioned_or(bot.DEFAULTPREFIX)(bot, message)

    try:
        data = await bot.config.find(message.guild.id)

        # Make sure we have a use able prefix
        if not data or "prefix" not in data:
            return commands.when_mentioned_or(bot.DEFAULTPREFIX)(bot, message)
        return commands.when_mentioned_or(data["prefix"])(bot, message)
    except exceptions.IdNotFound:
        return commands.when_mentioned_or(bot.DEFAULTPREFIX)(bot, message)


logging.basicConfig(level="INFO")
bot = commands.Bot(
    command_prefix=get_prefix,
    case_insensitive=True,
    description="A short sharp bot coded in python to aid the python "
    "developers with helping the community "
    "with discord.py related issues.",
)

# Use regex to parse mentions, much better than only supporting
# nickname mentions (<@!1234>)
# This basically ONLY matches a string that only consists of a mention
mention = re.compile(r"^<@!?(?P<id>\d+)>$")

logger = logging.getLogger(__name__)

bot.DEFAULTPREFIX = "py."
bot.menudocs_projects_id = config["menudocs_projects_id"]
bot.story_channel_id = config["story_channel_id"]
bot.dpy_help_channel_id = config["discord.py_help_channel"]

bot.remove_command("help")


@bot.event
async def on_ready():
    logger.info("I'm all up and ready like mom's spaghetti")

    try:
        await bot.config.get_all()
    except exceptions.PyMongoError as e:
        logger.error("An error occurred while fetching the config: %s" % e)
    else:
        logger.info("Database connection established")


@bot.event
async def on_message(message):
    # Ignore messages sent by bots
    if message.author.bot:
        return

    # Whenever the bot is tagged, respond with its prefix
    if match := mention.match(message.content):
        if int(match.group("id")) == bot.user.id:
            data = await bot.config._Document__get_raw(message.guild.id)
            if not data or "prefix" not in data:
                prefix = bot.DEFAULTPREFIX
            else:
                prefix = data["prefix"]

            await message.channel.send(
                f"My prefix here is `{prefix}`", delete_after=15
            )

    await bot.process_commands(message)


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
            result = f"```py\n{stdout.getvalue()}\n-- {obj}```"
            await ctx.send(result)
    except Exception as e:
        await ctx.send("".join(format_exception(e, e, e.__traceback__)))


@bot.command()
@commands.is_owner()
async def dbbackup(ctx):
    """Back up the database"""
    await ctx.send("https://giphy.com/gifs/christmas-3P0oEX5oTmrkY")

    backupDB = motor.motor_asyncio.AsyncIOMotorClient(
        config["mongo_url"]
    ).backup
    backupConfig = Document(backupDB, "config")
    backupKeywords = Document(backupDB, "keywords")
    backupQuiz = Document(backupDB, "quiz")
    backupCode = Document(backupDB, "code")
    backupQuizAnswers = Document(backupDB, "quizAnswers")
    backupStarboard = Document(backupDB, "starboard")

    for item in await bot.config.get_all():
        await backupConfig.upsert(item)

    for item in await bot.keywords.get_all():
        await backupKeywords.upsert(item)

    for item in await bot.quiz.get_all():
        await backupQuiz.upsert(item)

    for item in await bot.code.get_all():
        await backupCode.upsert(item)

    for item in await bot.quiz_answers.get_all():
        await backupQuizAnswers.upsert(item)

    for item in await bot.starboard.get_all():
        await backupStarboard.upsert(item)

    await ctx.send(
        "https://giphy.com/gifs/deliverance-vN3fMMSAmVwoo\n\n*Database backup complete*"
    )


# Load all extensions
if __name__ == "__main__":
    # Database initialization
    bot.db = motor.motor_asyncio.AsyncIOMotorClient(config["mongo_url"]).pyro

    bot.config = Document(bot.db, "config")
    bot.keywords = Document(bot.db, "keywords")
    bot.quiz = Document(bot.db, "quiz")
    bot.code = Document(bot.db, "code")
    bot.quiz_answers = Document(bot.db, "quizAnswers")
    bot.starboard = Document(bot.db, "starboard")

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

    bot.run(config["token"])
