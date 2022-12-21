import logging
from typing import Dict, List, Optional

import disnake
from alaric import Document
from bot_base import PrefixNotFound, BotContext
from bot_base.paginators.disnake_paginator import DisnakePaginator
from bot_base.wraps import WrappedMember
from disnake import Interaction
from disnake.ext import commands

from pyro import Pyro, checks
from pyro.db import Tag

log = logging.getLogger(__name__)


class Dropdown(disnake.ui.Select):
    def __init__(self):
        options = [
            disnake.SelectOption(
                label="Python",
                description="Anything Python related except bots.",
            ),
            disnake.SelectOption(
                label="Python discord bots",
                description="Anything todo with Python discord bots.",
            ),
            disnake.SelectOption(
                label="Javascript",
                description="Anything Javascript related except bots.",
            ),
            disnake.SelectOption(
                label="Javascript discord bots",
                description="Anything todo with Javascript discord bots.",
            ),
            disnake.SelectOption(
                label="Java",
                description="Anything Java related except bots.",
            ),
            disnake.SelectOption(
                label="Java discord bots",
                description="Anything todo with Java discord bots.",
            ),
            disnake.SelectOption(
                label="Coding",
                description="Anything general and coding related.",
            ),
            disnake.SelectOption(
                label="Misc",
                description="Anything not covered above.",
            ),
            disnake.SelectOption(
                label="Discord",
                description="Backwards compatibility.",
            ),
        ]

        super().__init__(
            placeholder="Choose your category",
            options=options,
        )


class DropdownView(disnake.ui.View):
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
    async def on_message(self, message: disnake.Message):
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

        log.info("Sending tag '%s'", tag.name)

        tag.uses += 1
        await self.tags_db.increment({"name": tag.name}, "uses", 1)

        await tag.send(message.channel, invoked_with=tag_name)

    @commands.slash_command()
    async def tag(self, inter):
        """Entry level tag intro."""
        pass

    @tag.sub_command(name="view")
    @commands.check_any(checks.can_eval(), checks.ensure_is_menudocs_staff())
    async def tag_view(
        self,
        inter: disnake.ApplicationCommandInteraction,
        tag: str = commands.Param(description="The tag you wish to view."),
    ):
        """View the provided tag."""
        tag: Optional[Tag] = self.tags.get(tag.casefold())
        if not tag:
            # No tag found with this name
            return await inter.send(
                ephemeral=True, content="The provided tag does not exist."
            )

        log.info("Sending tag '%s'", tag.name)

        tag.uses += 1
        await self.tags_db.increment({"name": tag.name}, "uses", 1)
        await tag.send(inter, invoked_with=tag.name)

    @tag.sub_command(name="create")
    @commands.check_any(checks.can_eval(), checks.ensure_is_menudocs_staff())
    async def tag_create(
        self,
        inter: disnake.ApplicationCommandInteraction,
        name: str = commands.Param(description="What should this tag be called?"),
        description: str = commands.Param(
            description="A 75 character or less description"
        ),
        content: str = commands.Param(description="This tags content."),
        override_existing: bool = commands.Param(
            description="Should this tag replace an existing one?", default=False
        ),
        should_embed: bool = commands.Param(
            description="Should this tag be sent in an embed?", default=False
        ),
    ):
        """Create a new tag."""
        if len(name.split(" ")) != 1:
            return await inter.send("Tag names cannot contain spaces.", ephemeral=True)

        if name in self.tags and not override_existing:
            return await inter.send(
                "A tag with this name already exists and you did not ask to override it, cancelling..",
                ephemeral=True,
            )

        if len(description) > 75:
            return await inter.send(
                "Description should be 75 characters or less. Cancelling.",
                ephemeral=True,
            )

        view: DropdownView = DropdownView(inter.author)
        await inter.send("Please choose your tag category", view=view, ephemeral=True)
        await view.wait()

        tag: Tag = Tag(
            name=name,
            content=content,
            creator_id=inter.author.id,
            description=description,
            is_embed=should_embed,
            category=view.result,
        )
        self.tags[name.casefold()] = tag
        await self.tags_db.upsert({"name": tag.name}, tag.to_dict())
        await inter.edit_original_message(
            f"I have created the tag `{name}` for you.", view=None
        )

    @tag.sub_command(name="repr")
    @commands.check_any(checks.can_eval(), checks.ensure_is_menudocs_staff())
    async def tag_repr(
        self,
        inter: disnake.ApplicationCommandInteraction,
        tag: str = commands.Param(description="The tag you wish to view."),
    ):
        """Send the raw tag."""
        tag: Optional[Tag] = self.tags.get(tag.casefold())
        if not tag:
            return await inter.send("No tag found with that name.", ephemeral=True)

        file: disnake.File = tag.as_file()
        await inter.send(f"Raw tag for `{tag}`", file=file, ephemeral=True)

    @tag.sub_command(name="delete")
    @commands.check_any(checks.can_eval(), checks.ensure_is_menudocs_staff())
    async def tag_delete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        tag: str = commands.Param(description="The tag you wish to view."),
    ):
        """Delete the given tag or tag alias."""
        tag_name = tag
        if tag_name not in self.tags:
            return await inter.send("Invalid tag provided.", ephemeral=True)

        is_alias = self.is_tag_alias(tag_name)

        tag_obj: Tag = self.tags.pop(tag_name.casefold())
        if is_alias:
            tag_obj.aliases.discard(tag_name)
            await self.tags_db.update({"name": tag_obj.name}, tag_obj.to_dict())

        else:
            # Primary tag
            for alias in tag_obj.aliases:
                self.tags.pop(alias, None)
            await self.tags_db.delete({"name": tag_name})

        await inter.send(
            f"Deleted that tag {'alias ' if is_alias else ''}for you!", ephemeral=True
        )

    @tag.sub_command(name="alias")
    @commands.check_any(checks.can_eval(), checks.ensure_is_menudocs_staff())
    async def tag_alias(
        self,
        inter: disnake.ApplicationCommandInteraction,
        existing_tag: str = commands.Param(description="The name of the existing tag."),
        new_alias: str = commands.Param(description="The new alias for the tag."),
    ):
        """Create tag aliases."""
        if len(new_alias.split(" ")) != 1:
            return await inter.send("Tag names cannot contain spaces.", ephemeral=True)

        if new_alias in self.tags:
            return await inter.send(
                "Tag alias would override an existing tag, cancelling.", ephemeral=True
            )

        tag: Optional[Tag] = self.tags.get(existing_tag)
        if not tag:
            return await inter.send("No tag found with this name.", ephemeral=True)

        tag.aliases.add(new_alias)
        self.tags[new_alias] = tag
        await self.tags_db.update({"name": tag.name}, tag.to_dict())

        await inter.send(
            f"Created an alias '`{new_alias}`' to pre-existing tag `{tag.name}`",
            ephemeral=True,
        )

    @tag.sub_command(name="list")
    async def tag_list(self, inter: disnake.ApplicationCommandInteraction):
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
                desc += f"`{tag.name}` - {tag.description}\n"

            desc += "\n"
            categories.append(desc)

        async def format_page(pages, page_number):
            embed = disnake.Embed(title=f"Pyro tags")
            embed.description = "".join(pages)

            embed.set_footer(text=f"Page {page_number}")
            return embed

        paginator: DisnakePaginator = DisnakePaginator(
            1,
            categories,
        )
        paginator.format_page = format_page
        await paginator.start(interaction=inter)

    @tag.sub_command(name="set_description")
    @commands.check_any(checks.can_eval(), checks.ensure_is_menudocs_staff())
    async def tag_set_desc(
        self,
        inter: disnake.ApplicationCommandInteraction,
        tag: str = commands.Param(description="The tag you wish to view."),
        description: str = commands.Param(
            description="The new description for this tag."
        ),
        override_existing: bool = commands.Param(
            description="Should this description replace an existing one?",
            default=False,
        ),
    ):
        """Modify the description for a tag."""
        try:
            tag: Tag = self.tags[tag]
        except KeyError:
            return await inter.send(
                "A tag with that name does not exist.", ephemeral=True
            )

        if tag.description and not override_existing:
            return await inter.send(
                "Cancelling tag modification as you do not want to override the existing description.",
                ephemeral=True,
            )

        if len(description) > 75:
            return await inter.send(
                "Description should be 75 characters or less. Please run the command again.",
                ephemeral=True,
            )

        tag.description = description
        await self.tags_db.upsert({"name": tag.name}, tag.to_dict())
        await inter.send(
            "I have changed the description of that tag for you.", ephemeral=True
        )

    @tag.sub_command(name="details")
    async def tag_details(
        self,
        inter: disnake.ApplicationCommandInteraction,
        tag: str = commands.Param(description="The tag you wish to view."),
    ):
        """Show a specific tags details."""
        try:
            tag: Tag = self.tags[tag]
        except KeyError:
            return await inter.send(
                "A tag with that name does not exist.", ephemeral=True
            )

        tag_desc = f"'{tag.description}'\n---\n" if tag.description else ""
        tag_aliases = ", ".join(tag.aliases) if tag.aliases else "No aliases"

        embed = disnake.Embed(
            title=f"Viewing tag `{tag.name}`",
            description=f"{tag_desc}Aliases: {tag_aliases}"
            f"\nCategory: {tag.category}\nCreated by: <@{tag.creator_id}>\n"
            f"Sent as embed? {tag.is_embed}\nUses: **{tag.uses}**\n"
            f"Content:\n{tag.content}",
        )
        await inter.send(embed=embed, ephemeral=True)

    @tag.sub_command(name="usage")
    async def tag_usage(self, inter: disnake.ApplicationCommandInteraction):
        """Show tags, sorted by usage."""
        all_tags: List[Tag] = await self.tags_db.get_all()
        all_tags: List[Tag] = sorted(all_tags, key=lambda x: x.uses, reverse=True)
        tag_lists: List[str] = [
            f"Used `{tag.uses}` time{'s' if tag.uses == 1 else ''} - __{tag.name}__\n"
            for tag in all_tags
        ]

        async def format_page(pages, page_number):
            embed = disnake.Embed(title=f"Pyro tags")
            embed.description = "".join(pages)

            embed.set_footer(text=f"Page {page_number}")
            return embed

        paginator: DisnakePaginator = DisnakePaginator(
            10,
            tag_lists,
        )
        paginator.format_page = format_page
        await paginator.start(interaction=inter)

    @tag_view.autocomplete("tag")
    @tag_repr.autocomplete("tag")
    @tag_delete.autocomplete("tag")
    @tag_details.autocomplete("tag")
    @tag_set_desc.autocomplete("tag")
    @tag_alias.autocomplete("existing_tag")
    async def get_tag_for(
        self,
        _,
        user_input: str,
    ):
        possible_choices = [
            v for v in self.tags.keys() if user_input.lower() in v.lower()
        ]

        if len(possible_choices) > 25:
            return []

        return possible_choices


def setup(bot):
    bot.add_cog(Tags(bot))
