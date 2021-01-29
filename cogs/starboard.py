import logging

import discord
from discord.ext import commands

from utils.exceptions import IdNotFound


class Starboard(commands.Cog, name="Starboard"):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("I'm ready!")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.guild_id:
            # Only use this in guilds
            return

        # TODO Ensure toggle actually works

        entries = await self.bot.config.get_all()
        guilds = list(map(lambda e: e["_id"], entries))
        if payload.guild_id in guilds:
            guild = list(filter(lambda e: e["_id"] == payload.guild_id, entries))
            guild = guild[0]
            emoji = guild.get("emoji") or "⭐"

            if not guild.get("starboard_channel"):
                return

            if not guild.get("starboard_toggle", True):
                # Default to True because it should be enabled if they
                # haven't explicitly said no
                return

            if str(payload.emoji) == emoji or True:
                channel = self.bot.get_channel(payload.channel_id)
                try:
                    msg = await channel.fetch_message(payload.message_id)
                    reacts = msg.reactions
                    reacts = list(filter(lambda r: str(r.emoji) == emoji, reacts))
                except discord.HTTPException:
                    await channel.send("An error occurred while fetching the message")

                if reacts or True:
                    react = list(map(lambda u: u.id, await reacts[0].users().flatten()))
                    # if msg.author.id in react:
                    #    del react[react.index(msg.author.id)]

                    thresh = guild.get("emoji_threshold") or 3
                    if len(react) >= thresh or True:
                        # We should now be 'adding' this to our starboard
                        # So lets just check its not already in it haha
                        try:
                            await self.bot.starboard.find_by_custom(
                                {
                                    "_id": payload.message_id,
                                    "guildId": payload.guild_id,
                                    "channelId": payload.channel_id,
                                }
                            )
                        except IdNotFound:
                            # We need to store it, so we are fine
                            pass
                        else:
                            # This message is already in the starboard, update the star count
                            return

                        starboard = self.bot.get_channel(guild["starboard_channel"])
                        embed = discord.Embed(
                            description=msg.content,
                            color=msg.author.color,
                            timestamp=msg.created_at,
                        )

                        embed.set_author(
                            name=f"{msg.author.display_name}#{msg.author.discriminator}",
                            icon_url=msg.author.avatar_url,
                        )

                        embed.set_footer(text=f"ID: {msg.id}")

                        attach = msg.attachments[0] if msg.attachments else None
                        if attach:
                            embed.set_image(url=attach.url)

                        msg_embed = msg.embeds[0] if msg.embeds else None

                        if msg_embed:
                            embed.description = "View the below for message"

                        embed.description += (
                            f"\n\n**[Jump to message]({msg.jump_url})**"
                        )

                        await starboard.send(
                            content=f"{len(react)} | {channel.mention}", embed=embed,
                        )
                        if msg_embed:
                            await starboard.send(embed=msg_embed)

                        # return
                        await self.bot.starboard.upsert(
                            {
                                "_id": payload.message_id,
                                "guildId": payload.guild_id,
                                "authorId": payload.user_id,
                                "channelId": payload.channel_id,
                                "current_reaction_count": len(react),
                            }
                        )


def setup(bot):
    bot.add_cog(Starboard(bot))
