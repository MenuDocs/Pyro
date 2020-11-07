import logging

from discord.ext import commands


class AutoHelp(commands.Cog, name="Autohelp"):
    def __init__(self, bot):
        self.bot = bot
        self.keywords = await self.bot.keywords.get_all()
        self.channels = [kw["channel"] for kw in self.keywords]
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("I'm ready!")

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.channel.id not in self.channels or msg.author.bot:
            return

        tokens = msg.content.split()
        for kw in await self.keywords.get_all():
            if set(kw["keywords"]).issubset(set(tokens)):
                await msg.channel.send(kw["response"])
                return


def setup(bot):
    bot.add_cog(AutoHelp(bot))
