import logging

import nextcord
from bot_base import BotContext
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

    @commands.Cog.listener()
    async def on_ready(self):
        log.info(f"{self.__class__.__name__}: Ready")

    @commands.command()
    @commands.guild_only()
    @commands.max_concurrency(1, BucketType.user)
    async def review_guild(self, ctx: BotContext):
        """Start the review process for your guild."""
        role_ids = [role.id for role in ctx.author.roles]
        if 917886722942062612 not in role_ids:
            return await ctx.send("You need to have Developer membership to use this.")

        if await self.bot.db.guild_reviews.find_by_custom(
            {"requester_id": ctx.author.id, "pending": True}
        ):
            return await ctx.send(
                "You already have a review marked as pending.\n"
                "If this is an error please let us know."
            )

        name = await ctx.author.get_input(
            description="What is your guilds name?", delete_after=False
        )
        if not name:
            return await ctx.send_basic_embed(
                "I've cancelled the process. Please start over."
            )

        purpose = await ctx.author.get_input(
            description="What is your guilds purpose? I.e. Whats it about.",
            delete_after=False,
        )
        if not purpose:
            return await ctx.send_basic_embed(
                "I've cancelled the process. Please start over."
            )

        specifics = await ctx.author.get_input(
            description="Any specifics we should know about?", delete_after=False
        )
        if not specifics:
            return await ctx.send_basic_embed(
                "I've cancelled the process. Please start over."
            )

        guild_invite = await ctx.author.get_input(
            description="Can we get an invite for your server please.",
            delete_after=False,
        )
        if not guild_invite:
            return await ctx.send_basic_embed(
                "I've cancelled the process. Please start over."
            )

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

        embed = nextcord.Embed(
            title=f"Guild review request for: `{ctx.author.display_name}`",
            description=f"Guild Name: `{name}`\n---\nPurpose: {purpose}\n---\n"
            f"Specifics: {specifics}\n---\nInvite: {guild_invite}",
        )

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
