import discord
from discord.ext import commands
import logging
import asyncio
import os
import json

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
if __name__ == "__main__":
	for ext in os.listdir("./cogs/"):
		if ext.endswith(".py") and not ext.startswith("_"):
			try:
				bot.load_extension(f"cogs.{ext[:-3]}")
			except Exception as e:
				logger.error(f"An error occured while loading extension: cogs.{ext[:-3]}")
				

bot.run(config["token"])
