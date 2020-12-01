import os
import random
import traceback
import typing
import logging
import asyncio

import emojis
import discord
from git import Repo
from discord.ext import commands

from utils.exceptions import IdNotFound


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
                description = ""
                for ext in os.listdir("./cogs/"):
                    if ext.endswith(".py") and not ext.startswith("_"):
                        try:
                            self.bot.unload_extension(f"cogs.{ext[:-3]}")
                            await asyncio.sleep(0.5)
                            self.bot.load_extension(f"cogs.{ext[:-3]}")
                            description += f"Reloaded: `{ext}`\n"
                        except Exception as e:
                            embed.add_field(
                                name=f"Failed to reload: `{ext}`", value=e,
                            )
                    await asyncio.sleep(0.5)
                embed.description = description
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
                        embed.description = f"Reloaded: `{ext}`"
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
        await ctx.send("Beginning the update")
        async with ctx.typing():
            repo = Repo(os.getcwd())
            repo.git.fetch()
            repo.git.pull()

            # attempt to reload all commands
            await asyncio.sleep(5)
            await self.reload(ctx)

            await ctx.send("Update complete!")

    @commands.group(
        name="starboard",
        aliases=["sb"],
        description="Configure the starboard for your server!",
        invoke_without_command=True,
    )
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def starboard(self, ctx):
        await ctx.invoke(self.bot.get_command("help"), entity="starboard")

    @starboard.command(
        name="toggle", description="Turn the starboard on or off for your guild.",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def sb_toggle(self, ctx):
        try:
            data = await self.bot.config.find(ctx.guild.id)
        except IdNotFound:
            await ctx.send(
                "You have not setup the starboard for this guild, please use the `starboard channel` command to do so."
            )
            return
        else:
            if not data.get("starboard_toggle"):
                data = {"_id": ctx.guild.id, "starboard_toggle": True}
                await ctx.send("I have turned the starboard `on` for you.")
            else:
                data = {"_id": ctx.guild.id, "starboard_toggle": False}
                await ctx.send("I have turned the starboard `off` for you.")
            await self.bot.config.upsert(data)

    @starboard.command(
        name="channel", description="Set the starboard channel for this guild!",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def sb_channel(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            await ctx.send(
                "I will attempt to set this guilds starboard channel to this channel as you failed to give me another "
                "channel. "
            )

        channel = channel or ctx.channel
        try:
            await channel.send("test", delete_after=0.05)
        except discord.HTTPException:
            await ctx.send(
                "I can not send a message to that channel! Please give me permissions and try again."
            )
            return

        try:
            data = await self.bot.config.find(ctx.guild.id)
        except IdNotFound:
            data = {
                "_id": ctx.guild.id,
                "starboard_channel": channel.id,
                "starboard_toggle": True,
            }
        else:
            data["starboard_channel"] = channel.id
        finally:
            await self.bot.config.upsert(data)
            await ctx.send("I have set the starboard channel for this guild!")

    @starboard.command(
        name="emoji", description="Make the starboard work with your own emoji!",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def sb_emoji(self, ctx, emoji: typing.Union[discord.Emoji, str] = None):
        if not emoji:
            await self.bot.config.upsert({"_id": ctx.guild.id, "emoji": None})
            await ctx.send("Reset your server's custom emoji.")
        elif isinstance(emoji, discord.Emoji):
            if not emoji.is_usable():
                await ctx.send("I can't use that emoji.")
                return

            await self.bot.config.upsert({"_id": ctx.guild.id, "emoji": str(emoji)})

            await ctx.send("Added your emoji.")
        else:
            emos = emojis.get(emoji)
            if emos:
                await self.bot.config.upsert({"_id": ctx.guild.id, "emoji": emoji})

                await ctx.send("Added your emoji.")
            else:
                await ctx.send("Please use a proper emoji.")

    @starboard.command(name="threshold", description="Choose your own emoji threshold.")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def sb_thresh(self, ctx, thresh: int = None):
        if not thresh:
            await self.bot.config.upsert({"_id": ctx.guild.id, "emoji_threshold": None})
            await ctx.send("Reset your server's custom emoji threshold.")
        else:
            await self.bot.config.upsert(
                {"_id": ctx.guild.id, "emoji_threshold": thresh}
            )

            await ctx.send("Added your threshold.")

    @commands.command(
        description="Ignore a specified channel. This does not respond to commands in the specified channel."
    )
    @commands.has_permissions(manage_messages=True)
    async def ignore(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel

        try:
            data = await self.bot.config.find(ctx.guild.id)
            if channel.id in data["ignored_channels"]:
                await ctx.send(
                    "This channel is already ignored. Use the `unignore` command to unignore it."
                )
                return
        except IdNotFound:
            await self.bot.config.insert(
                {"_id": ctx.guild.id, "ignored_channels": [channel.id]}
            )
            await ctx.send(
                "This channel has been ignored. You can use the `unignore` command to unignore it."
            )
            return

        await self.bot.config.upsert(
            {"_id": ctx.guild.id, "ignored_channels": channel.id}, option="push"
        )
        await ctx.send(
            "This channel has been ignored. You can use the `unignore` command to unignore it."
        )

    @commands.command(
        description="Unignores a previously ignored channel. Allows commands to be ran."
    )
    @commands.has_permissions(manage_messages=True)
    async def unignore(self, ctx, channel: discord.TextChannel):
        try:
            data = await self.bot.config.find(ctx.guild.id)
            if channel.id not in data["ignored_channels"]:
                await ctx.send(
                    "This channel is not ignored. You can use the `ignore` command to ignore it."
                )
                return

            await self.bot.config.upsert(
                {"_id": ctx.guild.id, "ignored_channels": channel.id}, option="pull"
            )
            await ctx.send("This channel has been unignored.")
        except IdNotFound:
            await ctx.send(
                "This channel is not ignored. You can use the `ignore` command to ignore it."
            )

    @commands.command(
        aliases=["gc"],
        description="Views the guild's config. Shows the starboard channels, ignored channels, prefix, starboard "
        "data, etc.",
    )
    @commands.has_permissions(manage_channels=True)
    async def guild_config(self, ctx):
        embed = discord.Embed(
            title=f"Configuration of {ctx.guild.name}",
            color=random.randint(0, 0xFFFFFF),
        )
        try:
            data = await self.bot.config.find(ctx.guild.id)
        except IdNotFound:
            await ctx.send("This guild does not have anything saved.")
        else:
            try:
                channels = map(
                    lambda c: self.bot.get_channel(c).mention, data["ignored_channels"]
                )
                data["ignored_channels"] = channels
            except KeyError:
                pass

            embed.description = "\n".join(
                (
                    f"{attr}: {val}".replace("_", " ").title()
                    for attr, val in data.items()
                )
            )
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Config(bot))
