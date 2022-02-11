import logging
from typing import Dict, List, Optional

import nextcord
from bot_base import PrefixNotFound, BotContext
from bot_base.db import Document
from bot_base.wraps import WrappedMember
from nextcord import Interaction
from nextcord.ext import commands, menus

from pyro import Pyro, checks
from pyro.db import Tag
from pyro.utils.pagination import TagsPageSource

log = logging.getLogger(__name__)


class Dropdown(nextcord.ui.Select):
    def __init__(self):
        options = [
            nextcord.SelectOption(
                label="Python",
                description="Anything Python related except bots.",
            ),
            nextcord.SelectOption(
                label="Python discord bots",
                description="Anything todo with Python discord bots.",
            ),
            nextcord.SelectOption(
                label="Javascript",
                description="Anything Javascript related except bots.",
            ),
            nextcord.SelectOption(
                label="Javascript discord bots",
                description="Anything todo with Javascript discord bots.",
            ),
            nextcord.SelectOption(
                label="Java",
                description="Anything Java related except bots.",
            ),
            nextcord.SelectOption(
                label="Java discord bots",
                description="Anything todo with Java discord bots.",
            ),
            nextcord.SelectOption(
                label="Coding",
                description="Anything general and coding related.",
            ),
            nextcord.SelectOption(
                label="Discord",
                description="Idk, ask Mandroc devs",
            ),
            nextcord.SelectOption(
                label="Misc",
                description="Anything not covered.",
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
            self.tags[tag.name.casefold()] = tag
            for alias in tag.aliases:
                self.tags[alias.casefold()] = tag

    def is_tag_alias(self, tag_name) -> bool:
        """
        Returns
        -------
        bool
            True if the given tag_name is
            actually an alias
        """
        tag: Tag = self.tags[tag_name.casefold()]
        return tag_name in tag.aliases

    @commands.Cog.listener()
    async def on_ready(self):
        log.info(f"{self.__class__.__name__}: Ready")

        await self.update_tags()

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        try:
            prefix = await self.bot.get_guild_prefix(message.guild.id)
        except (PrefixNotFound, AttributeError):
            prefix = self.bot.DEFAULT_PREFIX

        prefix = self.bot.get_case_insensitive_prefix(message.content, prefix)

        if not message.content.startswith(prefix):
            return

        tag_name = message.content.replace(prefix, "").split(" ")[0]
        tag: Optional[Tag] = self.tags.get(tag_name.casefold())
        if not tag:
            # No tag found with this name
            return

        log.info("Sending tag %s", tag.name)

        await tag.send(message.channel, invoked_with=tag_name)

    @commands.group(aliases=["tag"], invoke_without_command=True)
    async def tags(self, ctx: BotContext):
        """Entry level tag intro."""
        await ctx.send_help(ctx.command)

    @tags.command()
    @commands.check_any(checks.can_eval(), checks.ensure_is_menudocs_staff())
    async def create(self, ctx: BotContext, *, tag_name: str = None):
        """Create a new tag."""
        if not tag_name:
            tag_name = await ctx.get_input(
                description="What should this tag be called?"
            )
            if not tag_name:
                return await ctx.send_basic_embed("Cancelling tag creation.")

        if len(tag_name.split(" ")) != 1:
            return await ctx.send_basic_embed("Tag names cannot contain spaces.")

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

        tag_description = await ctx.get_input(
            description="Provide a description of 40 characters or less."
        )
        if not tag_description:
            return await ctx.send_basic_embed("Cancelling tag creation.")
        elif len(tag_description) > 40:
            return await ctx.send_basic_embed(
                "Description should be 40 characters or less."
            )

        tag_content = await ctx.get_input(
            description="What should the content for this tag be?"
        )
        if not tag_content:
            return await ctx.send_basic_embed("Cancelling tag creation.")

        view: DropdownView = DropdownView(ctx.author)  # type: ignore
        m = await ctx.send("Please choose your tag category", view=view)
        await view.wait()
        await m.delete()

        should_embed = await ctx.prompt("Should this tag be sent in an embed?")

        tag: Tag = Tag(
            name=tag_name,
            content=tag_content,
            creator_id=ctx.author.id,
            description=tag_description,  # type: ignore
            is_embed=bool(should_embed),
            category=view.result,
        )
        self.tags[tag_name.casefold()] = tag
        await self.tags_db.upsert_custom({"name": tag.name}, tag.to_dict())
        await ctx.send_basic_embed(
            f"I have created the tag `{tag_name}` for you.\n"
            f"`{ctx.prefix}{tag_name}` to invoke it."
        )

    @tags.command()
    @commands.check_any(checks.can_eval(), checks.ensure_is_menudocs_staff())
    async def repr(self, ctx: BotContext, *, tag_name: str = None):
        """Send the raw tag."""
        if not tag_name:
            return await ctx.send_basic_embed(
                "Please provide a tag name when calling this command."
            )

        tag: Optional[Tag] = self.tags.get(tag_name.casefold())
        if not tag:
            return await ctx.send_basic_embed("No tag found with that name.")

        await ctx.send(f"Raw tag for `{tag_name}`\n```py\n{repr(tag)}\n```")

    @tags.command()
    @commands.check_any(checks.can_eval(), checks.ensure_is_menudocs_staff())
    async def delete(self, ctx: BotContext, *, tag_name: str = None):
        """Delete the given tag or tag alias."""
        if not tag_name:
            return await ctx.send_basic_embed(
                "Please provide a tag name when calling this command."
            )

        if tag_name not in self.tags:
            return await ctx.send_basic_embed("Invalid tag provided.")

        check_delete = await ctx.prompt(
            f"Are you sure you want to delete the tag `{tag_name}`?"
        )
        if not check_delete:
            return await ctx.send_basic_embed("That was close, cancelling deletion.")

        is_alias = self.is_tag_alias(tag_name)

        tag: Tag = self.tags.pop(tag_name.casefold())
        if is_alias:
            tag.aliases.discard(tag_name)
            await self.tags_db.update_by_custom({"name": tag.name}, tag.to_dict())

        else:
            # Primary tag
            for alias in tag.aliases:
                self.tags.pop(alias, None)
            await self.tags_db.delete_by_custom({"name": tag_name})

        await ctx.send_basic_embed(
            f"Deleted that tag {'alias ' if is_alias else ''}for you!"
        )

    @tags.command()
    @commands.check_any(checks.can_eval(), checks.ensure_is_menudocs_staff())
    async def alias(self, ctx: BotContext, tag_name: str = None, new_alias: str = None):
        """Create tag aliases."""
        if not tag_name:
            tag_name = await ctx.get_input(
                description="What is the name of the tag to be aliased?"
            )
            if not tag_name:
                return await ctx.send_basic_embed("Cancelling alias creation.")

        if len(tag_name.split(" ")) != 1:
            return await ctx.send_basic_embed("Tag names cannot contain spaces.")

        tag: Optional[Tag] = self.tags.get(tag_name)
        if not tag:
            return await ctx.send_basic_embed("No tag found with this name.")

        if not new_alias:
            new_alias = await ctx.get_input(
                description="What is the name of the alias?"
            )
            if not new_alias:
                return await ctx.send_basic_embed("Cancelling alias creation.")

        tag.aliases.add(new_alias)
        self.tags[new_alias] = tag
        await self.tags_db.update_by_custom({"name": tag.name}, tag.to_dict())

        await ctx.send_basic_embed(
            f"Created an alias '`{new_alias}`' to pre-existing tag `{tag.name}`"
        )

    @tags.command(aliases=["all"])
    async def list(self, ctx: BotContext):
        """List all current tags."""
        categories: list[str] = []
        tag_category_splits: dict[str, list[Tag]] = {}
        all_tags: List[Tag] = await self.tags_db.get_all()
        for tag in all_tags:
            try:
                tag_category_splits[tag.category].append(tag)
            except KeyError:
                tag_category_splits[tag.category] = [tag]

        for cat, tags in tag_category_splits.items():
            desc = f"**{cat}**\n---\n"
            for tag in tags:
                desc += f"`{ctx.prefix}{tag.name}` - {tag.description}\n"

            desc += "\n"
            categories.append(desc)

        pages = menus.ButtonMenuPages(
            source=TagsPageSource(
                self.bot,
                categories,
            ),
            clear_buttons_after=True,
        )
        await pages.start(ctx)


def setup(bot):
    bot.add_cog(Tags(bot))
