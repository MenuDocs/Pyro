import logging
from typing import List

import nextcord
from bot_base import BotContext
from bot_base.wraps import WrappedMember
from nextcord import AllowedMentions
from nextcord.ext import commands
from nextcord.ext.commands import BucketType

from bot import Pyro
from db import GuildReview

log = logging.getLogger(__name__)


class Review(commands.Cog):
    def __init__(self, bot):
        self.bot: Pyro = bot
        self.team_role_id: int = 659897739844517931
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
    @commands.max_concurrency(1, BucketType.user)
    async def review_guild(self, ctx: BotContext):
        """Start the review process for your guild."""
        # role_ids = [role.id for role in ctx.author.roles]
        # if 917886722942062612 not in role_ids:
        #     return await ctx.send("You need to have Developer membership to use this.")

        if ctx.author.id != 203104843479515136:
            return await ctx.send("Not yet.")

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

        if await self.bot.db.guild_reviews.find_by_custom(
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
                return await ctx.send_basic_embed()

        guild_review: GuildReview = GuildReview(
            name=name,
            purpose=purpose,
            specifics=specifics,
            guild_invite=guild_invite,
            requester_id=ctx.author.id,
        )

        category = await self.bot.get_or_fetch_channel(self.review_category_id)
        guild = ctx.guild
        team = guild.get_role(self.team_role_id)

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
            f"{ctx.author.mention} - <@&{self.team_role_id}>",
            embed=embed,
            allowed_mentions=allowed_mentions,
        )


def setup(bot):
    bot.add_cog(Review(bot))
