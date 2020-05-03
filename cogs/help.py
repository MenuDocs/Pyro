import discord
from discord.ext import commands
from discord.ext import buttons
import os
import random
import re
import math
import logging

class Help(commands.Cog, name="Help command"):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("I'm ready!")

    @commands.command(
        name="help", aliases=["h", "commands"], description="The help command!"
    )
    async def help_command(self, ctx, entity):
    	"""
    	Sends paginated help command or help for
    	an existing entity.
    	"""
        


def setup(bot):
    bot.add_cog(Help(bot))
