import discord
from discord.ext import commands
import logging
import asyncio
import json
import os
import motor.motor_asyncio

from cogs._mongo import Document

with open("config.json", "r") as f:
    config = json.load(f)


async def get_prefix(bot, message):
    # If dm's
    if not message.guild:
        return commands.when_mentioned_or("-")(bot, message)

    data = await bot.db.config.find_one({"_id": message.guild.id})
    # Make sure we have a useable prefix
    if not data or "prefix" not in data:
        return commands.when_mentioned_or("-")(bot, message)
    return commands.when_mentioned_or(data["prefix"])(bot, message)


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
    bot.db = motor.motor_asyncio.AsyncIOMotorClient(config["mongo url"]).pyro
    logger.info("Database connection established")

    bot.config = Document(bot.db, "config")

@bot.event
async def on_message(message):
    #Ignore messages sent by yourself
    if message.author.id == bot.user.id:
        return

    #Whenever the bot is tagged, respond with its prefix
    if message.content.startswith(f"<@!{bot.user.id}>"):
        data = await bot.db.config.find_one({"_id": message.guild.id})
        if not data or 'prefix' not in data:
            prefix = '-'
        else:
            prefix = data['prefix']
        await message.channel.send(f"My prefix here is `{prefix}`", delete_after=15)

    await bot.process_commands(message)


# Commands used to showcase & test
@bot.command()
async def add(ctx, id, *, str):
    await bot.config.update({"_id": id, "message": str})


@bot.command()
async def find(ctx, id):
    await ctx.send(await bot.config.find(id))


@bot.command()
async def getall(ctx):
    print(await bot.config.get_all())


@bot.command()
async def delete(ctx, id):
    await bot.config.delete(id)


if __name__ == "__main__":
    # Loop over every file in the cogs dir
    for file in os.listdir("./cogs"):
        # If the file is a python file and does not start with an _
        # assume it is a cog and attempt to load it
        if file.endswith(".py") and not file.startswith("_"):
            try:
                bot.load_extension(f"cogs.{file[:-3]}")
            except Exception as e:
                logger.error(f"Failed to load cog: {file[:-3]}\n{e}")

    bot.run(config["token"])
