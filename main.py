import discord
from discord.ext import commands
import logging
import asyncio
import os
import json
import motor.motor_asyncio

from utils.mongo import Document

with open("config.json", "r") as f:
    config = json.load(f)


async def get_prefix(bot, message):
    # If dm's
    if not message.guild:
        return commands.when_mentioned_or("py.")(bot, message)

    try:
        data = await bot.config.find(message.guild)
        # Make sure we have a useable prefix
        if not data or "prefix" not in data:
            return commands.when_mentioned_or("py.")(bot, message)
        return commands.when_mentioned_or(data["prefix"])(bot, message)
    except:
        return commands.when_mentioned_or("py.")(bot, message)


logging.basicConfig(level="INFO")
bot = commands.Bot(
    command_prefix=get_prefix,
    case_insensitive=True,
    description="A short sharp bot coded in python to aid the python developers with helping the community with discord.py related issues.",
)

logger = logging.getLogger(__name__)

bot.colors = {
    "WHITE": 0xFFFFFF,
    "AQUA": 0x1ABC9C,
    "GREEN": 0x2ECC71,
    "BLUE": 0x3498DB,
    "PURPLE": 0x9B59B6,
    "LUMINOUS_VIVID_PINK": 0xE91E63,
    "GOLD": 0xF1C40F,
    "ORANGE": 0xE67E22,
    "RED": 0xE74C3C,
    "NAVY": 0x34495E,
    "DARK_AQUA": 0x11806A,
    "DARK_GREEN": 0x1F8B4C,
    "DARK_BLUE": 0x206694,
    "DARK_PURPLE": 0x71368A,
    "DARK_VIVID_PINK": 0xAD1457,
    "DARK_GOLD": 0xC27C0E,
    "DARK_ORANGE": 0xA84300,
    "DARK_RED": 0x992D22,
    "DARK_NAVY": 0x2C3E50,
}
bot.color_list = [c for c in bot.colors.values()]
bot.remove_command("help")


@bot.event
async def on_ready():
    logger.info("I'm all up an ready like mom's spaghetti")

    # Database initialization
    bot.db = motor.motor_asyncio.AsyncIOMotorClient(config["mongo_url"]).pyro
    logger.info("Database connection established")

    bot.config = Document(bot.db, "config")


@bot.event
async def on_message(message):
    # Ignore messages sent by bots
    if message.author.bot:
        return

    # Whenever the bot is tagged, respond with its prefix
    if message.content.startswith(f"<@!{bot.user.id}>") and len(message.content) == len(
        f"<@!{bot.user.id}>"
    ):
        data = await bot.config.__get_raw(message.guild.id)
        if not data or "prefix" not in data:
            prefix = "py."
        else:
            prefix = data["prefix"]
        await message.channel.send(f"My prefix here is `{prefix}`", delete_after=15)

    await bot.process_commands(message)


# Load all extensions
if __name__ == "__main__":
    for ext in os.listdir("./cogs/"):
        if ext.endswith(".py") and not ext.startswith("_"):
            try:
                bot.load_extension(f"cogs.{ext[:-3]}")
            except Exception as e:
                logger.error(
                    f"An error occured while loading extension: cogs.{ext[:-3]}, {repr(e)}"
                )

    bot.run(config["token"])
