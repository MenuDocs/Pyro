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
    name='prefix',
    aliases=['changeprefix','setprefix'],
    description='Change your guilds prefix!',
    usage="<prefix>"
    )
    @commands.has_guild_permissions(administrator=True)
    async def prefix(self, ctx, *, pre='-'):
        self.bot.config.update({"_id": ctx.guild.id, "prefix": pre})
        await ctx.send(f"The guild prefix has been set to `{pre}`. Use `{pre}prefix <prefix>` to change it again!")

def setup(bot):
	bot.add_cog(Config(bot))
