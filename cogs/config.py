import discord
from discord.ext import commands
import logging
import os
import asyncio
from git import Repo


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
        try:
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
        except Exception as e:
            await ctx.send(f"{e}")

    @commands.command(
        name="update", description="Automatically updates the bot from github!",
    )
    @commands.is_owner()
    async def update_bot(self, ctx):
        async with ctx.typing():
            repo = Repo(os.getcwd())
            # repo.git.checkout("development") # Make sure to be on right branch before pulling it
            # uncomment the above once branches merge
            # in the future it should be master IG
            repo.git.fetch()
            repo.git.pull()

            # attempt to reload all commands
            await self.reload(ctx)


def setup(bot):
    bot.add_cog(Config(bot))
