import logging
import re

import discord
from discord.ext import commands

from utils.util import Pag

BASE_MENUDOCS_URL = "https://github.com/menudocs"
MAIN_GUILD = 416512197590777857
PROJECT_GUILD = 566131499506860045
MENUDOCS_GUILD_IDS = (MAIN_GUILD, PROJECT_GUILD)
PYTHON_HELP_CHANNEL_IDS = (
    621912956627582976,
    621913007630319626,
    479465622850371606,
    416522595958259713,
)


def ensure_is_menudocs_guild():
    async def check(ctx):
        if not ctx.guild or ctx.guild.id not in MENUDOCS_GUILD_IDS:
            return False
        return True

    return commands.check(check)


def ensure_is_menudocs_project_guild():
    async def check(ctx):
        if not ctx.guild or ctx.guild.id != PROJECT_GUILD:
            return False
        return True

    return commands.check(check)


def extract_repo(regex):
    return regex.group("repo") or "pyro"


class Menudocs(commands.Cog):
    """A cog devoted to operations within the Menudocs guild"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

        self.issue_regex = re.compile(r"##(?P<number>[0-9]+)\s?(?P<repo>[a-zA-Z0-9]*)")
        self.pr_regex = re.compile(r"\$\$(?P<number>[0-9]+)\s?(?P<repo>[a-zA-Z0-9]*)")
        self.injected_self = re.compile(
            r"@(client|bot)\.command\(\)\n(async def .*\(self, ctx.*\):)"
        )

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("I'm ready!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not message.guild or message.guild.id not in MENUDOCS_GUILD_IDS:
            # Not in menudocs
            return

        issue_regex = self.issue_regex.search(message.content)
        if issue_regex is not None:
            repo = extract_repo(issue_regex)
            number = issue_regex.group("number")
            url = f"{BASE_MENUDOCS_URL}/{repo}/issues/{number}"
            await message.channel.send(url)

        pr_regex = self.pr_regex.search(message.content)
        if pr_regex is not None:
            repo = extract_repo(pr_regex)
            number = pr_regex.group("number")
            url = f"{BASE_MENUDOCS_URL}/{repo}/pulls/{number}"
            await message.channel.send(url)

        # Only process in python help channels
        if message.channel.id not in PYTHON_HELP_CHANNEL_IDS:
            return

        await self.process_injected_self(message)

    async def process_injected_self(self, message):
        """
        Look in a message and attempt to auto-help on
        instances where members send code NOT in a cog
        that also contains self
        """
        injected_self = self.injected_self.search(message.content)
        if injected_self is None:
            # Don't process
            return

        initial_func = injected_self.group(2)
        fixed_func = initial_func.replace("self,", "")
        if "( c" in fixed_func:
            fixed_func = fixed_func.replace("( c", "(c")

        # We need to process this
        embed = discord.Embed(
            description="Looks like your defining a command with `self` as the first argument "
            "without using the correct decorator. Likely you want to remove `self` as this only "
            "applies to commands defined within a class (Cog).\nYou should change it as per the following:"
            f"\n\n**Old**\n`{initial_func}`\n**New | Fixed**\n`{fixed_func}`",
            timestamp=message.created_at,
            color=0x26F7FD,
        )
        embed.set_author(name="Pyro Auto Helper", icon_url=message.guild.me.avatar_url)
        embed.set_footer(text="Believe this is incorrect? Let Skelmis know.")

        await message.channel.send(
            f"{message.author.mention} this might help.", embed=embed, delete_after=30
        )

    @commands.command()
    @ensure_is_menudocs_guild()
    async def init(self, ctx):
        """Sends a helpful embed about how to fix import errors."""
        embed = discord.Embed(
            title="Seeing something like?\n`ModuleNotFoundError: No module named 'utils.utils'`\nRead on!",
            description="""
            In order to fix import issues, please add an empty file called
            `__init__.py` in your directory you are attempting to import from.
            If you are following our tutorials this is likely `utils`
            
            This happens because python is not aware of your folder
            being 'importable', by adding this file we explicitly
            declare it 'importable'. This generally resolves this issue.
            """,
        )
        await ctx.send(embed=embed)

    @commands.command()
    @ensure_is_menudocs_guild()
    async def pypi(self, ctx):
        """Sends a helpful embed about how to correctly download packages."""
        embed = discord.Embed(
            title="Trying to `pip install` something and getting the following?\n`Could not find a version that "
            "satisfies the requirement <package here>`",
            description="""
                Most likely the package you are trying to install isn't named
                the same as what you import. `discord.py` can be seen as an example
                here since you `import discord` and `pip install discord.py`
                
                A simple way to fix this is to google `pypi <package you want>`
                This will 9 times out of 10 provide the pypi page for said package,
                which will clearly indicate the correct way to install it.
                """,
        )
        await ctx.send(embed=embed)

    @commands.command()
    @ensure_is_menudocs_project_guild()
    async def story(self, ctx):
        """Creates the current story for the project discord."""
        channel = self.bot.get_channel(861209220536074250)
        messages = await channel.history(limit=None, oldest_first=True).flatten()
        story = " ".join([message.content.lower() for message in messages])
        story = story.capitalize()

        # Stats
        data = {}
        for message in messages:
            if message.author.name in data:
                data[message.author.name] += 1
            else:
                data[message.author.name] = 1

        data = sorted(data.items(), key=lambda x: x[1], reverse=True)

        story += "\n\n"
        for i in range(len(data)):
            story += f"{data[i][0]}, Messages contributed to story: {data[i][1]} \n"

        pager = Pag(
            title=f"Here is the current story from {channel.name}",
            entries=[story[i : i + 2000] for i in range(0, len(story), 2000)],
            length=1,
            prefix="```py\n",
            suffix="```",
        )

        await pager.start(ctx)


def setup(bot):
    bot.add_cog(Menudocs(bot))
