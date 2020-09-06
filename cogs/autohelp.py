import logging

from discord.ext import commands


class AutoHelp(commands.Cog, name="Autohelp"):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("I'm ready!")
        self.keywords = self.bot.keywords

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.channel.id != self.bot.dpy_help_channel_id or msg.author.bot:
            return

        tokens = msg.content.split()
        for kw in await self.keywords.get_all():
            if set(kw["keywords"]).issubset(set(tokens)):
                await msg.channel.send(kw["response"])
                return


def setup(bot):
    bot.add_cog(AutoHelp(bot))
