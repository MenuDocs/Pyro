import logging
from typing import Dict, List, Optional

import nextcord
from bot_base import PrefixNotFound
from bot_base.db import Document
from nextcord.ext import commands

from bot import Pyro
from db import Tag

log = logging.getLogger(__name__)


class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot: Pyro = bot

        self.tags: Dict[str, Tag] = {}
        self.tags_db: Document = self.bot.db.tags

    async def update_tags(self) -> None:
        """
        Updates the locally cached tags
        """
        all_tags: List[Tag] = await self.tags_db.get_all()
        for tag in all_tags:
            self.tags[tag.name] = tag

    @commands.Cog.listener()
    async def on_ready(self):
        log.info(f"{self.__class__.__name__}: Ready")

        await self.update_tags()

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        try:
            prefix = self.bot.get_guild_prefix(message.guild.id)
        except PrefixNotFound:
            prefix = self.bot.DEFAULT_PREFIX

        prefix = self.bot.get_case_insensitive_prefix(message.content, prefix)

        if not message.content.startswith(prefix):
            return

        tag_name = message.content.replace(prefix, "").split(" ")[0]
        tag: Optional[Tag] = self.tags.get(tag_name)
        if not tag:
            # No tag found with this name
            return

        await tag.send(message.channel)


def setup(bot):
    bot.add_cog(Tags(bot))
