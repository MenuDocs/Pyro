import logging
import random
import re
from string import Template
from typing import List

import disnake
from bot_base import BotContext
from bot_base.wraps import WrappedChannel
from disnake.ext import commands

from pyro.bot import Pyro
from pyro.checks import (
    MAIN_GUILD,
    MENUDOCS_GUILD_IDS,
    MENUDOCS_PROJECTIONS_CHANNEL,
    MENUDOCS_SUGGESTIONS_CHANNEL,
    MENUDOCS_UNVERIFIED_ROLE,
    PYTHON_HELP_CHANNEL_IDS,
    MenuDocsCog,
    ensure_is_menudocs_project_guild,
)

log = logging.getLogger(__name__)

BASE_MENUDOCS_URL = "https://github.com/menudocs"


def extract_repo(regex):
    return regex.group("repo") or "pyro"


class MenuDocs(MenuDocsCog):
    """A cog devoted to operations within the Menudocs guild"""

    def __init__(self, bot):
        self.bot: Pyro = bot
        self.logger = logging.getLogger(__name__)

        self.issue_regex = re.compile(r"##(?P<number>[0-9]+)\s?(?P<repo>[a-zA-Z0-9]*)")
        self.pr_regex = re.compile(r"\$\$(?P<number>[0-9]+)\s?(?P<repo>[a-zA-Z0-9]*)")

        # TODO Add a way to delete embeds

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("I'm ready!")

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        if not message.guild or message.guild.id not in MENUDOCS_GUILD_IDS:
            # Not in menudocs
            return

        issue_regex = self.issue_regex.search(message.content)
        if issue_regex is not None:
            repo = extract_repo(issue_regex)
            number = issue_regex.group("number")
            url = f"{BASE_MENUDOCS_URL}/{repo}/issues/{number}"
            await message.channel.send(url)

        pr_regex = self.pr_regex.search(message.content)
        if pr_regex is not None:
            repo = extract_repo(pr_regex)
            number = pr_regex.group("number")
            url = f"{BASE_MENUDOCS_URL}/{repo}/pull/{number}"
            await message.channel.send(url)

    @commands.Cog.listener()
    async def on_thread_create(self, thread) -> None:
        if not thread.guild or thread.guild.id not in MENUDOCS_GUILD_IDS:
            # Not in menudocs
            return

        if thread.parent_id not in PYTHON_HELP_CHANNEL_IDS:
            # Not a python help channel
            return

        await thread.join()

    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member):
        if after.guild.id != MAIN_GUILD:
            # Not in menudocs
            return

        if before.roles == after.roles:
            # If roles are the same
            return

        welcome_messages = [
            "$MEMBER just showed up. Hold my beer.",
            "Where's $MEMBER? In the server!",
            "Welcome, $MEMBER. Stay awhile and listen.",
            "We've been expecting you, $MEMBER.",
            "$MEMBER just joined. Can I get a heal?",
            "$MEMBER just joined the server - glhf!",
            "Ermagherd. $MEMBER has joined us!",
            "Mission Control! $MEMBER has successfully landed!",
        ]

        projections = after.guild.get_channel(MENUDOCS_PROJECTIONS_CHANNEL)
        unverified_role = after.guild.get_role(MENUDOCS_UNVERIFIED_ROLE)
        message = Template(random.choice(welcome_messages)).safe_substitute(
            {"MEMBER": f"**{after}**"}
        )
        embed = disnake.Embed(description=message, colour=disnake.Colour.green())

        if unverified_role in before.roles and unverified_role not in after.roles:
            await projections.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member) -> None:
        if member.guild.id != MAIN_GUILD:
            # Not in menudocs
            return

        leave_messages = [
            "$MEMBER has quit. Party's over.",
            "Ermagherd. $MEMBER has just left us here.",
            "Brace yourselves. $MEMBER just abandoned the server.",
            "$MEMBER just left. Can you come back?",
            "Whoopsies! $MEMBER left us!",
            "Nooooooo, $MEMBER closed the door.",
            "Commander, we've lost $MEMBER!",
            "Is this a loss? $MEMBER left.",
        ]

        message = Template(random.choice(leave_messages)).safe_substitute(
            {"MEMBER": f"**{member}**"}
        )
        projections = member.guild.get_channel(MENUDOCS_PROJECTIONS_CHANNEL)
        embed = disnake.Embed(description=message, colour=disnake.Colour.red())

        await projections.send(embed=embed)

    def extract_code(self, message: disnake.Message) -> List[str]:
        """Extracts all codeblocks to str"""
        content: List[str] = []
        current = []
        parsed_lst: List[str] = message.content.split("\n")

        is_codeblock = False
        for item in parsed_lst:
            # Only keep items with content from codeblocks
            if "```" in item:
                is_codeblock = not is_codeblock

                if not is_codeblock:
                    content.append("\n".join(current))
                    current = []

                continue

            if is_codeblock:
                current.append(item)

        return content

    @commands.command(aliases=["hc", "huhcount"])
    @ensure_is_menudocs_project_guild()
    async def huh_count(self, ctx: BotContext) -> None:
        """Count the huh's!"""
        mappin: dict[disnake.Member, int] = {}
        channel: WrappedChannel = await self.bot.get_or_fetch_channel(
            566133462986391553
        )
        async for message in channel.history():
            try:
                mappin[message.author] += 1
            except KeyError:
                mappin[message.author] = 1

        sorted_mappin: dict[disnake.Member, int] = dict(
            sorted(mappin.items(), key=lambda item: item[1], reverse=True)
        )
        desc = "**Huh count**\n-----\n\n"
        for k, v in sorted_mappin.items():
            desc += f"{k.mention} - {v}\n"

        await ctx.send_basic_embed(desc)


def setup(bot):
    bot.add_cog(MenuDocs(bot))
