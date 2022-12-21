import logging
from typing import List

import disnake
from bot_base import BotContext
from bot_base.wraps import WrappedMember
from disnake import AllowedMentions, Interaction
from disnake.ext import commands
from disnake.ext.commands import BucketType

from pyro.bot import Pyro
from pyro.checks import MenuDocsCog
from pyro.db import GuildReview, BotReview

log = logging.getLogger(__name__)


class Dropdown(disnake.ui.Select):
    def __init__(self, is_guild=True):
        if is_guild:
            options = [
                disnake.SelectOption(
                    label="Clubs",
                    description="Coding, Gaming etc",
                    # emoji="🟥",
                ),
                disnake.SelectOption(
                    label="Social",
                    description="Twitch, YouTube etc",
                    # emoji="🟩",
                ),
                disnake.SelectOption(
                    label="Misc",
                    description="Support server, Development support etc",
                    # emoji="🟦",
                ),
            ]
        else:
            options = [
                disnake.SelectOption(
                    label="Memes",
                    description="A bot devoted to the funnier side of life",
                    # emoji="🟥",
                ),
                disnake.SelectOption(
                    label="Multi Purpose",
                    # emoji="🟩",
                ),
                disnake.SelectOption(
                    label="Moderation",
                    # emoji="🟦",
                ),
                disnake.SelectOption(
                    label="Reaction roles",
                    # emoji="🟦",
                ),
                disnake.SelectOption(
                    label="Misc",
                    description="Anything not listed",
                    # emoji="🟦",
                ),
            ]

        super().__init__(
            placeholder="Choose your genre",
            options=options,
        )


class DropdownView(disnake.ui.View):
    def __init__(self, author: WrappedMember, is_guild=True):
        super().__init__(timeout=60)
        self._author: WrappedMember = author
        self.dropdown: Dropdown = Dropdown(is_guild)
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


class Review(MenuDocsCog):
    def __init__(self, bot):
        self.bot: Pyro = bot
        self.review_role_id: int = 939373151844958228
        self.review_category_id: int = 925723996585087016

    @staticmethod
    async def get_input(author: WrappedMember, desc: str) -> str:
        out = await author.get_input(description=desc, delete_after=False)
        if not out:
            raise TimeoutError

        return out

    @commands.Cog.listener()
    async def on_ready(self):
        log.info(f"{self.__class__.__name__}: Ready")

    @commands.command()
    @commands.guild_only()
    async def close(self, ctx: BotContext, *, summary):
        """Close a review"""
        if ctx.author.id not in {203104843479515136, 271612318947868673}:
            return await ctx.send_basic_embed(
                "You do not have permission to run this command."
            )

        review: GuildReview = await self.bot.db.guild_reviews.find(
            {"channel_id": ctx.channel.id}
        )
        if not review:
            review: BotReview = await self.bot.db.bot_reviews.find(
                {"channel_id": ctx.channel.id}
            )
            if not review:
                return await ctx.send_basic_embed(
                    "Doesn't look like this channel is a review channel!"
                )

        try:
            review_requester = await self.bot.get_or_fetch_user(review.requester_id)
            await review_requester.send_basic_embed(
                "Hey, we have closed your review request. "
                f"Please find your summary below.\n---\n{summary}"
            )
        except disnake.Forbidden:
            await ctx.author.send(
                "Couldn't tell that person about closing there review, sorry!"
            )

        review.closing_summary = summary
        if isinstance(review, GuildReview):
            await self.bot.db.guild_reviews.upsert(
                {"channel_id": ctx.channel.id}, review.to_dict()
            )
        else:
            await self.bot.db.bot_reviews.upsert(
                {"channel_id": ctx.channel.id}, review.to_dict()
            )

        review_channel = await self.bot.get_or_fetch_channel(review.channel_id)
        await review_channel.delete(reason="Review is finished.")

    @commands.command()
    @commands.guild_only()
    @commands.max_concurrency(1, BucketType.user)
    async def review_guild(self, ctx: BotContext):
        """Start the review process for your guild."""
        role_ids = [role.id for role in ctx.author.roles]
        if 917886722942062612 not in role_ids:
            return await ctx.send("You need to have Developer membership to use this.")

        questions: List[str] = [
            "What is the name of the guild you wish to get reviewed?",
            "Is there any specifics you would like to tell us?",
            "What is your server about/for?",
            "What is your guilds current member count?",
            "What is the main focuses that you’d like criticism on?",
            "How many text channels do you have? How many of those are accessible by everyone?",
            "What is the invite to your server?",
        ]
        answers: List[str] = []
        prompts: List[str] = [
            "Do you understand that you may need to provide a higher privilege role "
            "so we’re able to have a look at your private text channels/voice channels?",
            "Do you understand that all reviews are simply opinionated suggestions "
            "that are based on previous and current knowledge of server ownership?",
        ]

        if await self.bot.db.guild_reviews.find(
            {"requester_id": ctx.author.id, "pending": True}
        ):
            return await ctx.send(
                "You already have a review marked as pending.\n"
                "If this is an error please let us know."
            )

        for question in questions:
            try:
                answers.append(await self.get_input(ctx.author, question))
            except TimeoutError:
                return await ctx.author.send_basic_embed("Cancelling the process.")

        for prompt in prompts:
            yes_or_no = await ctx.author.prompt(prompt, delete_after=False)
            if not yes_or_no:
                return await ctx.author.send_basic_embed("Cancelling this process.")

        view: DropdownView = DropdownView(ctx.author)
        m = await ctx.author.send(
            "Please answer this about your guilds genre.", view=view
        )
        await view.wait()
        await m.edit(view=None)
        guild_review: GuildReview = GuildReview(
            requester_id=ctx.author.id,
            name=answers[0],
            purpose=answers[2],
            specifics=answers[1],
            guild_invite=answers[6],
            text_channel_question=answers[5],
            criticism_question=answers[4],
            member_count=answers[3],
            guild_type=view.result,
        )

        category = await self.bot.get_or_fetch_channel(self.review_category_id)
        guild = ctx.guild
        team = guild.get_role(self.review_role_id)

        chan = await guild.create_text_channel(
            name=f"{ctx.author.display_name} - Guild Review",
            overwrites={
                guild.default_role: disnake.PermissionOverwrite(read_messages=False),
                guild.me: disnake.PermissionOverwrite(read_messages=True),
                ctx.author: disnake.PermissionOverwrite(read_messages=True),
                team: disnake.PermissionOverwrite(read_messages=True),
            },
            category=category,
        )
        guild_review.channel_id = chan.id

        await self.bot.db.guild_reviews.upsert(
            {"requester_id": ctx.author.id}, guild_review.to_dict()
        )

        embed = guild_review.as_embed(ctx.author.display_name)

        allowed_mentions: AllowedMentions = AllowedMentions.none()
        allowed_mentions.roles = [team]
        allowed_mentions.users = [ctx.author]

        await chan.send(
            f"{ctx.author.mention} - <@&{self.review_role_id}>",
            embed=embed,
            allowed_mentions=allowed_mentions,
        )

        await ctx.author.send_basic_embed(
            "That is all done. Please send any further correspondence in the channel I mentioned you in."
        )

    @commands.command()
    @commands.guild_only()
    @commands.max_concurrency(1, BucketType.user)
    async def review_bot(self, ctx: BotContext):
        """Start the review process for your bot."""
        role_ids = [role.id for role in ctx.author.roles]
        if 917886722942062612 not in role_ids:
            return await ctx.send("You need to have Developer membership to use this.")

        questions: List[str] = [
            "What is the name of the bot you wish to get reviewed?",
            "Is there any specifics you would like to tell us?",
            "What is your bot about/for?",
            "What is the main focuses that you’d like criticism on?",
            "What is the invite for your bot?",
        ]
        answers: List[str] = []
        prompts: List[str] = [
            "Do you understand that you may need to provide a higher privilege role "
            "so we’re able to have a look at your private features?",
            "Do you understand that all reviews are simply opinionated suggestions "
            "that are based on previous and current knowledge of bot development?",
        ]

        if await self.bot.db.bot_reviews.find(
            {"requester_id": ctx.author.id, "pending": True}
        ):
            return await ctx.send(
                "You already have a review marked as pending.\n"
                "If this is an error please let us know."
            )

        for question in questions:
            try:
                answers.append(await self.get_input(ctx.author, question))
            except TimeoutError:
                return await ctx.author.send_basic_embed("Cancelling the process.")

        for prompt in prompts:
            yes_or_no = await ctx.author.prompt(prompt, delete_after=False)
            if not yes_or_no:
                return await ctx.author.send_basic_embed("Cancelling this process.")

        view: DropdownView = DropdownView(ctx.author, is_guild=False)
        m = await ctx.author.send(
            "Please answer this about your bots genre.", view=view
        )
        await view.wait()
        await m.edit(view=None)
        bot_review: BotReview = BotReview(
            requester_id=ctx.author.id,
            bot_type=view.result,
            name=answers[0],
            specifics=answers[1],
            purpose=answers[2],
            criticism_question=answers[3],
            bot_invite=answers[4],
        )

        category = await self.bot.get_or_fetch_channel(self.review_category_id)
        guild = ctx.guild
        team = guild.get_role(self.review_role_id)

        chan = await guild.create_text_channel(
            name=f"{ctx.author.display_name} - Bot Review",
            overwrites={
                guild.default_role: disnake.PermissionOverwrite(read_messages=False),
                guild.me: disnake.PermissionOverwrite(read_messages=True),
                ctx.author: disnake.PermissionOverwrite(read_messages=True),
                team: disnake.PermissionOverwrite(read_messages=True),
            },
            category=category,
        )
        bot_review.channel_id = chan.id

        await self.bot.db.bot_reviews.upsert(
            {"requester_id": ctx.author.id}, bot_review.to_dict()
        )

        embed = bot_review.as_embed(ctx.author.display_name)

        allowed_mentions: AllowedMentions = AllowedMentions.none()
        allowed_mentions.roles = [team]
        allowed_mentions.users = [ctx.author]

        await chan.send(
            f"{ctx.author.mention} - <@&{self.review_role_id}>",
            embed=embed,
            allowed_mentions=allowed_mentions,
        )

        await ctx.author.send_basic_embed(
            "That is all done. Please send any further correspondence in the channel I mentioned you in."
        )


def setup(bot):
    bot.add_cog(Review(bot))
