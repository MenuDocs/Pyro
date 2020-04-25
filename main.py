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

logging.basicConfig(level="INFO")
bot = commands.Bot(command_prefix=commands.when_mentioned_or(config["prefix"]), description="ok")

logger = logging.getLogger(__name__)


# Ready event. more should go here for
# the database initialization.
@bot.event
async def on_ready():
    logger.info("I'm all up an ready like mom's spaghetti")

    # Database initialization
    bot.db = motor.motor_asyncio.AsyncIOMotorClient(config['mongo url']).pyro
    logger.info("Database connection established")

    bot.config = Document(bot.db, "config")


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

#############################
###                       ###
###    REMAINING CODE.    ###
###                       ###
#############################

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
