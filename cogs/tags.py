import logging
from typing import Dict, List, Optional

import nextcord
from bot_base import PrefixNotFound, BotContext
from bot_base.db import Document
from bot_base.wraps import WrappedMember
from nextcord import Interaction
from nextcord.ext import commands

from pyro import Pyro, checks
from pyro.db import Tag

log = logging.getLogger(__name__)


class Dropdown(nextcord.ui.Select):
    def __init__(self):
        options = [
            nextcord.SelectOption(label="Python"),
            nextcord.SelectOption(label="Python discord bots"),
            nextcord.SelectOption(label="Javascript"),
            nextcord.SelectOption(label="Javascript discord bots"),
            nextcord.SelectOption(label="Java"),
            nextcord.SelectOption(label="Java discord bots"),
            nextcord.SelectOption(label="Coding"),
            nextcord.SelectOption(
                label="Discord",
                description="Idk, ask Mandroc devs",
            ),
            nextcord.SelectOption(
                label="Misc",
                description="Anything else",
            ),
        ]

        super().__init__(
            placeholder="Choose your category",
            options=options,
        )


class DropdownView(nextcord.ui.View):
    def __init__(self, author: WrappedMember):
        super().__init__(timeout=60)
        self._author: WrappedMember = author
        self.dropdown: Dropdown = Dropdown()
        self.add_item(self.dropdown)
        self._timeout = False

    async def interaction_check(self, interaction: Interaction):
        if self._author.id != interaction.user.id:
            return

        self.stop()

    async def on_timeout(self) -> None:
        self._timeout = True

    @property
    def result(self):
        return self.dropdown.values[0] if not self._timeout else None


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

    @commands.group(aliases=["tag"], invoke_without_command=True)
    async def tags(self, ctx: BotContext):
        """Entry level tag intro."""
        await ctx.send_help()

    @tags.command()
    @commands.check_any(checks.can_eval())
    async def create(self, ctx: BotContext, *, tag_name: str = None):
        """Create a new tag."""
        if not tag_name:
            tag_name = await ctx.get_input(
                description="What should this tag be called?"
            )
            if not tag_name:
                return await ctx.send_basic_embed("Cancelling tag creation.")

        if self.bot.get_command(tag_name):
            return await ctx.send_basic_embed(
                f"You cannot create a tag called `{tag_name}` "
                f"as a command with that name already exists."
            )

        if tag_name in self.tags:
            wants_to_override = await ctx.prompt(
                "A tag with this name already exists, are you sure you wish to override it?"
            )
            if not wants_to_override:
                return await ctx.send_basic_embed("Cancelling tag creation.")

        tag_content = await ctx.get_input("What should the content for this tag be?")
        if not tag_content:
            return await ctx.send_basic_embed("Cancelling tag creation.")

        tag_description = await ctx.get_input(
            "Provide a description of 40 characters or less."
        )
        if not tag_description or (
            isinstance(tag_description, str) and len(tag_description) > 40
        ):
            return await ctx.send_basic_embed("Cancelling tag creation.")

        should_embed = await ctx.prompt("Should this tag be sent in an embed?")

        view: DropdownView = DropdownView(ctx.author)  # type: ignore
        m = await ctx.author.send("Please choose your tag category", view=view)
        await view.wait()
        await m.edit(view=None)

        tag: Tag = Tag(
            name=tag_name,
            content=tag_content,
            creator_id=ctx.author.id,
            description=tag_description,  # type: ignore
            is_embed=bool(should_embed),
            category=view.result,
        )
        await self.tags_db.upsert_custom({"name": tag.name}, tag.to_dict())
        await ctx.send_basic_embed(
            f"I have created the tag `{tag_name}` for you.\n"
            f"`{ctx.prefix}{tag_name}` to invoke it."
        )

    @tags.command()
    async def repr(self, ctx: BotContext, *, tag_name: str = None):
        """Send the raw tag."""
        if not tag_name:
            return await ctx.send_basic_embed(
                "Please provide a tag name when calling this command."
            )

        tag: Optional[Tag] = self.tags.get(tag_name)
        if not tag:
            return await ctx.send_basic_embed("No tag found with that name.")

        await ctx.send(f"Raw tag for `{tag_name}`\n```py\n{repr(tag)}\n```")


def setup(bot):
    bot.add_cog(Tags(bot))
