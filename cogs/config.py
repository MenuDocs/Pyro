import os
import logging

import asyncio
import discord
from git import Repo
from discord.ext import commands


class Config(commands.Cog, name="Configuration"):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("I'm ready!")

    @commands.command(
        name="prefix",
        aliases=["changeprefix", "setprefix"],
        description="Change your guilds prefix!",
        usage="[prefix]",
    )
    @commands.has_guild_permissions(manage_guild=True)
    async def prefix(self, ctx, *, prefix="py."):
        await self.bot.config.upsert({"_id": ctx.guild.id, "prefix": prefix})
        await ctx.send(
            f"The guild prefix has been set to `{prefix}`. Use `{prefix}prefix [prefix]` to change it again!"
        )

    @commands.command(
        name="reload", description="Reload all/one of the bots cogs!", usage="[cog]",
    )
    @commands.is_owner()
    async def reload(self, ctx, cog=None):
        if not cog:
            async with ctx.typing():
                embed = discord.Embed(
                    title="Reloading all cogs!",
                    color=0x808080,
                    timestamp=ctx.message.created_at,
                )
                for ext in os.listdir("./cogs/"):
                    if ext.endswith(".py") and not ext.startswith("_"):
                        try:
                            self.bot.unload_extension(f"cogs.{ext[:-3]}")
                            await asyncio.sleep(0.5)
                            self.bot.load_extension(f"cogs.{ext[:-3]}")
                            embed.add_field(
                                name=f"Reloaded: `{ext}`",
                                value=f"`{ext}` reloaded, but what did you expect to happen? Like really..",
                            )
                        except Exception as e:
                            embed.add_field(
                                name=f"Failed to reload: `{ext}`", value=e,
                            )
                    await asyncio.sleep(0.5)
                await ctx.send(embed=embed)
        else:
            async with ctx.typing():
                embed = discord.Embed(
                    title=f"Reloading {cog}!",
                    color=0x808080,
                    timestamp=ctx.message.created_at,
                )
                cog = cog.lower()
                ext = f"{cog}.py"
                if not os.path.exists(f"./cogs/{ext}"):
                    embed.add_field(
                        name=f"Failed to reload: `{ext}`",
                        value="This cog file does not exist.",
                    )
                elif ext.endswith(".py") and not ext.startswith("_"):
                    try:
                        self.bot.unload_extension(f"cogs.{ext[:-3]}")
                        await asyncio.sleep(0.5)
                        self.bot.load_extension(f"cogs.{ext[:-3]}")
                        embed.add_field(
                            name=f"Reloaded: `{ext}`",
                            value=f"`{ext}` reloaded, but what did you expect to happen? Like really..",
                        )
                    except Exception:
                        desired_trace = traceback.format_exc()
                        embed.add_field(
                            name=f"Failed to reload: `{ext}`", value=desired_trace,
                        )
                await asyncio.sleep(0.5)
            await ctx.send(embed=embed)

    @commands.command(
        name="update", description="Automatically updates the bot from github!",
    )
    @commands.is_owner()
    async def update_bot(self, ctx):
        async with ctx.typing():
            repo = Repo(os.getcwd())
            repo.git.checkout(
                "development"
            )  # Make sure to be on right branch before pulling it
            repo.git.fetch()
            repo.git.pull()

            # attempt to reload all commands
            await self.reload(ctx)

    @commands.group(
        name="starboard",
        description="Configure the starboard for your server!",
        invoke_without_command=True
    )
    @commands.has_permissions(manage_messages=True)
    async def starboard(self, ctx, channel: discord.TextChannel = None):
        current = await self.bot.config.find(ctx.guild.id)
        if current.get('starboard_channel') and not channel:
            await self.bot.config.upsert(
                {"_id": ctx.guild.id, "starboard_channel": None}
            )

            await ctx.send("Turned off starboard.")
        elif channel:
            await self.bot.config.upsert(
                {"_id": ctx.guild.id, "starboard_channel": channel.id}
            )

            await ctx.send(f"Set starboard channel to {channel.mention}")
        else:
            await ctx.send("Please specify a channel.")

    @starboard.command(
        name="emoji",
        description="Make the starboard work with your own emoji!"
    )
    @commands.has_permissions(manage_messages=True)
    async def sb_emoji(self, ctx, emoji: discord.Emoji = None):
        if not emoji:
            await self.bot.config.upsert(
                {"_id": ctx.guild.id, "emoji": None}
            )
            await ctx.send("Reset your server's custom emoji.")
        else:
            if not emoji.is_usable():
                await ctx.send("I can't use that emoji.")
                return

            await self.bot.config.upsert(
                {"_id": ctx.guild.id, "emoji": str(emoji)}
            )

            await ctx.send("Added your emoji.")

    @starboard.command(
        name="threshold",
        description="Choose your own emoji threshold."
    )
    @commands.has_permissions(manage_messages=True)
    async def sb_thresh(self, ctx, thresh: int = None):
        if not thresh:
            await self.bot.config.upsert(
                {"_id": ctx.guild.id, "emoji_threshold": None}
            )
            await ctx.send("Reset your server's custom emoji threshold.")
        else:
            await self.bot.config.upsert(
                {"_id": ctx.guild.id, "emoji_threshold": thresh}
            )

            await ctx.send("Added your threshold.")


def setup(bot):
    bot.add_cog(Config(bot))
