import asyncio
import discord
from discord.ext import commands


class Story(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def story(self, ctx):
        """
        Get the current story from #One-word-story
        !story
        """
        if ctx.guild.id != self.bot.menudocs_projects_id:
            # Only work in projects guild
            return
        async with ctx.typing():
            channel = self.bot.get_channel(self.bot.story_channel_id)
            messages = await channel.history(limit=None, oldest_first=True).flatten()
            story = " ".join([message.content for message in messages])

            # Stats
            data = {}
            for message in messages:
                if message.author.name in data:
                    data[message.author.name] += 1
                else:
                    data[message.author.name] = 1

            data = sorted(data.items(), key=lambda x: x[1], reverse=True)

            for chunk in [story[i : i + 2000] for i in range(0, len(story), 2000)]:
                embed = discord.Embed(
                    title=f"Here is the current story from {channel.name}",
                    description=chunk,
                )
                await ctx.send(embed=embed)
                await asyncio.sleep(0.5)

            em = discord.Embed()
            em.add_field(name="Current Word Count:", value=len(messages))
            for i in range(len(data)):
                em.add_field(
                    name=data[i][0],
                    value=f"Messages contributed to story: {data[i][1]}",
                )

            await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Story(bot))
