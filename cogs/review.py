import logging
from typing import List

import nextcord
from bot_base import BotContext
from bot_base.wraps import WrappedMember
from nextcord import AllowedMentions, Interaction
from nextcord.ext import commands
from nextcord.ext.commands import BucketType

from pyro.bot import Pyro
from pyro.checks import MenuDocsCog
from pyro.db import GuildReview

log = logging.getLogger(__name__)


class Dropdown(nextcord.ui.Select):
    def __init__(self):
        options = [
            nextcord.SelectOption(
                label="Clubs",
                description="Coding, Gaming etc",
                # emoji="🟥",
            ),
            nextcord.SelectOption(
                label="Social",
                description="Twitch, YouTube etc",
                # emoji="🟩",
            ),
            nextcord.SelectOption(
                label="Misc",
                description="Support server, Development support etc",
                # emoji="🟦",
            ),
        ]
        super().__init__(
            placeholder="Choose your guilds genre",
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


class Review(MenuDocsCog):
    def __init__(self, bot):
        self.bot: Pyro = bot
        self.review_role_id: int = 928276706568052797
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

        guild_review: GuildReview = await self.bot.db.guild_reviews.find_by_custom(
            {"channel_id": ctx.channel.id}
        )
        if not guild_review:
            # TODO Add bot reviews here
            return await ctx.send_basic_embed(
                "Doesn't look like this channel is a review channel!"
            )

        try:
            review_requester = await self.bot.get_or_fetch_user(
                guild_review.requester_id
            )
            await review_requester.send_basic_embed(
                "Hey, we have closed your review request. "
                f"Please find your summary below.\n---\n{summary}"
            )
        except nextcord.Forbidden:
            await ctx.author.send(
                "Couldn't tell that person about closing there review, sorry!"
            )

        guild_review.closing_summary = summary
        await self.bot.db.guild_reviews.upsert_custom(
            {"channel_id": ctx.channel.id}, guild_review.to_dict()
        )

        review_channel = await self.bot.get_or_fetch_channel(guild_review.channel_id)
        await review_channel.delete(reason="Review is finished.")

    @commands.command()
    @commands.guild_only()
    @commands.max_concurrency(1, BucketType.user)
    async def review_guild(self, ctx: BotContext):
        """Start the review process for your guild."""
        # role_ids = [role.id for role in ctx.author.roles]
        # if 917886722942062612 not in role_ids:
        #     return await ctx.send("You need to have Developer membership to use this.")

        if ctx.author.id not in {203104843479515136, 271612318947868673}:
            return await ctx.send("Not yet available to the public.")

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

        # TODO Re-enable
        # if await self.bot.db.guild_reviews.find_by_custom(
        #     {"requester_id": ctx.author.id, "pending": True}
        # ):
        #     return await ctx.send(
        #         "You already have a review marked as pending.\n"
        #         "If this is an error please let us know."
        #     )

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

        try:
            guild_review: GuildReview = GuildReview(
                requester_id=ctx.author.id,
                name=answers[0],
                purpose=answers[2],
                specifics=answers[1],
                guild_invite=answers[6],
                text_channel_question=answers[5],
                criticism_question=answers[4],
                member_count=int(answers[3]),
                guild_type=view.result,
            )
        except ValueError:
            return await ctx.author.send_basic_embed(
                "Cancelling the command. Please provide an actual member count."
            )

        category = await self.bot.get_or_fetch_channel(self.review_category_id)
        guild = ctx.guild
        team = guild.get_role(self.review_role_id)

        chan = await guild.create_text_channel(
            name=f"{ctx.author.display_name} - Guild Review",
            overwrites={
                guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
                guild.me: nextcord.PermissionOverwrite(read_messages=True),
                ctx.author: nextcord.PermissionOverwrite(read_messages=True),
                team: nextcord.PermissionOverwrite(read_messages=True),
            },
            category=category,
        )
        guild_review.channel_id = chan.id

        await self.bot.db.guild_reviews.upsert_custom(
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


def setup(bot):
    bot.add_cog(Review(bot))
