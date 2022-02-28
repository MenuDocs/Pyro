import logging
from typing import List

import nextcord
from nextcord.ext import commands

from pyro.bot import Pyro
from pyro.checks import ALLOWED_HELP_CHANNELS

log = logging.getLogger(__name__)


class Autohelp(commands.Cog):
    def __init__(self, bot):
        self.bot: Pyro = bot

    @commands.Cog.listener()
    async def on_ready(self):
        log.info(f"{self.__class__.__name__}: Ready")

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        # We don't technically need this here anymore
        # if not message.guild or message.guild.id not in AUTOHELP_ALLOWED_DISCORDS:
        #     # Not in an allowed discord
        #     return

        if message.author.bot:
            return

        # Only process in python help channels
        if message.channel.id not in ALLOWED_HELP_CHANNELS:
            if not isinstance(message.channel, nextcord.Thread):
                return

            if message.channel.parent_id not in ALLOWED_HELP_CHANNELS:
                return

            # Process shit in threads if its parent is an allowed channel

        await self.bot.auto_help.process_message(message)


def setup(bot):
    bot.add_cog(Autohelp(bot))
