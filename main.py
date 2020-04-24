import discord
from discord.ext import commands
import logging
import asyncio
import json

extensions = ["cogs.docs"]

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

#############################
###                       ###
###    REMAINING CODE.    ###
###                       ###
#############################

# Load all extensions
for ext in extensions:
    bot.load_extension(ext)

bot.run(config["token"])
