import logging
import re

import discord
from discord.ext import commands

BASE_MENUDOCS_URL = "https://github.com/menudocs/"
MENUDOCS_GUILD_IDS = (416512197590777857, 566131499506860045)


def ensure_is_menudocs_guild():
    async def check(ctx):
        if not ctx.guild or ctx.guild.id not in MENUDOCS_GUILD_IDS:
            return False
        return True

    return commands.check(check)


class Menudocs(commands.Cog):
    """A cog devoted to operations with the Menudocs guild"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

        self.pyro_issue_regex = re.compile(r"##(?P<number>[0-9]+)")
        self.pyro_pr_regex = re.compile(r"\$\$(?P<number>[0-9]+)")

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("I'm ready!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not message.guild or message.guild.id not in MENUDOCS_GUILD_IDS:
            # Not in menudocs
            return

        pyro_issue_regex = self.pyro_issue_regex.search(message.content)
        if pyro_issue_regex is not None:
            url = f"{BASE_MENUDOCS_URL}pyro/issues/"
            await message.channel.send(url + pyro_issue_regex.group("number"))

        pyro_pr_regex = self.pyro_pr_regex.search(message.content)
        if pyro_pr_regex is not None:
            url = f"{BASE_MENUDOCS_URL}pyro/pulls/"
            await message.channel.send(url + pyro_pr_regex.group("number"))


def setup(bot):
    bot.add_cog(Docs(bot))
