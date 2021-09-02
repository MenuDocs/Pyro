import asyncio
import io
import os
import re
import logging
import textwrap
import contextlib
from pathlib import Path
from traceback import format_exception

import hikari
import motor.motor_asyncio

# noinspection PyPackageRequirements
import tanjun

from utils import exceptions, Document
from utils.util import clean_code

mongo_url = os.getenv("MONGO")
token = os.getenv("TOKEN")

"""
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
"""


logging.basicConfig(
    format="%(levelname)s | %(asctime)s | %(module)s | %(message)s",
    datefmt="%d/%m/%Y %I:%M:%S %p",
    level=logging.INFO,
)

DEFAULTPREFIX = "py."
bot = hikari.GatewayBot(token, intents=hikari.Intents.ALL)
command_client = (
    tanjun.Client.from_gateway_bot(bot)
    .add_prefix("'")
    .load_modules(*Path("./components").glob("*.py"))
    # .set_prefix_getter(get_prefix)
)
command_client.set_human_only(True)


logger = logging.getLogger(__name__)

# Use regex to parse mentions, much better than only supporting
# nickname mentions (<@!1234>)
# This basically ONLY matches a string that only consists of a mention
mention = re.compile(r"^<@!?(?P<id>\d+)>$")


@bot.listen()
async def on_start(event: hikari.StartedEvent):
    logger.info("I'm all up and ready like mom's spaghetti")


@bot.listen()
async def on_closed(event: hikari.StoppedEvent):
    logger.info("Bot has stopped")


@bot.listen()
async def on_message(event: hikari.GuildMessageCreateEvent):
    message = event.message
    # Ignore messages sent by bots
    if event.is_bot:
        return

    return

    if message.guild_id:
        try:
            guild_config = await bot.config.find(message.guild_id)
            if message.channel.id in guild_config["ignored_channels"]:
                return
        except exceptions.IdNotFound:
            pass
        except KeyError:
            pass

    # Whenever the bot is tagged, respond with its prefix
    if match := mention.match(message.content):
        if int(match.group("id")) == bot.get_me().id:
            if message.guild_id:
                data = await bot.config.find(message.guild_id)
                if data and "prefix" in data:
                    prefix = data["prefix"]
                else:
                    prefix = DEFAULTPREFIX
            else:
                prefix = DEFAULTPREFIX

            m = await message.respond(f"My prefix here is `{prefix}`")
            await asyncio.sleep(15)
            await m.delete()


# Load all extensions
if __name__ == "__main__":
    # Database initialization
    """
    bot.db = motor.motor_asyncio.AsyncIOMotorClient(mongo_url).pyro

    bot.config = Document(bot.db, "config")
    bot.keywords = Document(bot.db, "keywords")
    bot.quiz = Document(bot.db, "quiz")
    bot.code = Document(bot.db, "code")
    bot.quiz_answers = Document(bot.db, "quizAnswers")
    bot.starboard = Document(bot.db, "starboard")
    bot.tictactoe = Document(bot.db, "tictactoe")
    """

    bot.run(
        asyncio_debug=True,
        propagate_interrupts=True,
        coroutine_tracking_depth=20,
    )
