from discord.ext import commands

class Test(commands.Cog, name="Test"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(description="I like trains.")
    async def testcmd(self, ctx, ok):
        """
        testcmd is a group for testing (wtf??? testcmd group??? wow)
        """
        await ctx.send("ok")

    @testcmd.command()
    async def realtestcmd(self, ctx, ok):
        """
        realtestcmd is a command. Hooray!
        """
        await ctx.send(ok)


def setup(bot):
    bot.add_cog(Test(bot))
