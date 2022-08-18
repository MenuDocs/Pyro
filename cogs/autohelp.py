import logging

import disnake
from disnake.ext import commands

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
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return

        # Only process in python help channels
        if message.channel.id not in ALLOWED_HELP_CHANNELS:
            if not isinstance(message.channel, disnake.Thread):
                return

            if message.channel.parent_id not in ALLOWED_HELP_CHANNELS:
                return

            # Process shit in threads if its parent is an allowed channel

        # Disable this for now as the outputted 'fixed' code is munted
        # await self.bot.auto_help.process_message(message)


def setup(bot):
    bot.add_cog(Autohelp(bot))
