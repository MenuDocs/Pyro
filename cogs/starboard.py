import discord
from discord.ext import commands

import logging

class Starboard(commands.Cog, name="Starboard"):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("I'm ready!")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        entries = await self.bot.config.get_all()
        guilds = list(map(lambda e: e["_id"], entries))
        if payload.guild_id in guilds:
            guild = list(
                filter(
                    lambda e: e["_id"] == payload.guild_id,
                    entries
                )
            )
            guild = guild[0]
            emoji = guild.get("emoji") or "⭐"

            if not guild.get("starboard_channel"):
                return

            if str(payload.emoji) == emoji:
                try:
                    channel = self.bot.get_channel(payload.channel_id)
                    msg = await channel.fetch_message(payload.message_id)
                    reacts = msg.reactions
                    reacts = list(
                        filter(lambda r: str(r.emoji) == emoji, reacts)
                    )
                except discord.HTTPException:
                    await channel.send(
                        "An error occured while fetching the message"
                    )
                if reacts:
                    react = list(
                        map(
                            lambda u: u.id, await reacts[0].users().flatten()
                        )
                    )
                    if msg.author.id in react:
                        del react[react.index(msg.author.id)]

                    thresh = guild.get("emoji_threshold") or 3
                    if len(react) >= thresh:
                        starboard = self.bot.get_channel(
                            guild["starboard_channel"]
                        )

                        embed = discord.Embed(
                            title="Jump to message",
                            url=msg.jump_url,
                            description=msg.content,
                            color=msg.author.color
                        )

                        embed.set_author(
                            name=msg.author.display_name,
                            icon_url=msg.author.avatar_url
                        )

                        attach = msg.attachments[0] if msg.attachments \
                            else None

                        image = attach or msg.embeds[0] if msg.embeds else None

                        if image:
                            embed.set_image(url=image)

                        await starboard.send(
                            content=f"{emoji} {channel.mention}",
                            embed=embed
                        )


def setup(bot):
    bot.add_cog(Starboard(bot))