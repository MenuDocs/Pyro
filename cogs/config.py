import discord
from discord.ext import commands
import logging


class Config(commands.Cog):
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
    @commands.has_guild_permissions(administrator=True)
    async def prefix(self, ctx, *, prefix="py."):
        await self.bot.config.update({"_id": ctx.guild.id, "prefix": prefix})
        await ctx.send(
            f"The guild prefix has been set to `{prefix}`. Use `{prefix}prefix [prefix]` to change it again!"
        )

    @commands.group(
    name="testing",
    aliases=['test', 't'],
    description="Testing groups on the help command",
    usage=",Sub command"
    )
    async def test(self, ctx):
        pass

    @test.command(
    name="testtwo",
    description="group testing",
    usage="Subsub boi"
    )
    async def testtwo(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Config(bot))
