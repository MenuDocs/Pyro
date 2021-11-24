import logging
import re
from typing import Union, List

import nextcord
from axew import AxewClient, BaseAxewException
from nextcord.ext import commands
from nextcord.ext.commands import Greedy

from utils.util import Pag

BASE_MENUDOCS_URL = "https://github.com/menudocs"
MAIN_GUILD = 416512197590777857
PROJECT_GUILD = 566131499506860045
MENUDOCS_GUILD_IDS = (MAIN_GUILD, PROJECT_GUILD)
PYTHON_HELP_CHANNEL_IDS = (
    621912956627582976,  # discord.py
    621913007630319626,  # python
    702862760052129822,  # pyro
    416522595958259713,  # commands (main dc)
)
CODE_REVIEWER, PROFICIENT, TEAM = (
    850330300595699733,  # Code Reviewer
    479199775590318080,  # Proficient
    659897739844517931,  # ⚔ Team
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


def ensure_is_menudocs_staff():
    async def check(ctx):
        if not commands.has_any_role(CODE_REVIEWER, PROFICIENT, TEAM):
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

        self.axew = AxewClient()

        self.issue_regex = re.compile(r"##(?P<number>[0-9]+)\s?(?P<repo>[a-zA-Z0-9]*)")
        self.pr_regex = re.compile(r"\$\$(?P<number>[0-9]+)\s?(?P<repo>[a-zA-Z0-9]*)")
        self.requires_self_removal = re.compile(
            r"@(client|bot)\.command\(\)\n(async def .*\(self, ctx.*\):)"
        )
        self.command_requires_self_addition = re.compile(
            r"@commands\.command\(\)\n(async def .*\()(.*)(\).*:)"
        )
        self.event_requires_self_addition = re.compile(
            r"@commands\.Cog\.listener\(\)\n(async def .*\()(.*)(\).*:)"
        )

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("I'm ready!")

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message) -> None:
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
            url = f"{BASE_MENUDOCS_URL}/{repo}/pull/{number}"
            await message.channel.send(url)

        # Only process in python help channels
        if message.channel.id not in PYTHON_HELP_CHANNEL_IDS:
            return

        await self.process_requires_self_removal(message)
        await self.process_requires_self_addition(message)

    @commands.Cog.listener()
    async def on_thread_join(self, thread) -> None:
        if not thread.guild or thread.guild.id not in MENUDOCS_GUILD_IDS:
            # Not in menudocs
            return

        if thread.parent_id not in PYTHON_HELP_CHANNEL_IDS:
            # Not a python help channel
            return

        await thread.join()

    async def process_requires_self_removal(self, message):
        """
        Look in a message and attempt to auto-help on
        instances where members send code NOT in a cog
        that also contains self
        """
        injected_self = self.requires_self_removal.search(message.content)
        if injected_self is None:
            # Don't process
            return

        initial_func = injected_self.group(2)
        fixed_func = initial_func.replace("self,", "")
        if "( c" in fixed_func:
            fixed_func = fixed_func.replace("( c", "(c")

        # We need to process this
        embed = nextcord.Embed(
            description="Looks like your defining a command with `self` as the first argument "
            "without using the correct decorator. Likely you want to remove `self` as this only "
            "applies to commands defined within a class (Cog).\nYou should change it as per the following:"
            f"\n\n**Old**\n`{initial_func}`\n**New | Fixed**\n`{fixed_func}`",
            timestamp=message.created_at,
            color=0x26F7FD,
        )
        embed.set_author(name="Pyro Auto Helper", icon_url=message.guild.me.avatar.url)
        embed.set_footer(text="Believe this is incorrect? Let Skelmis know.")

        await message.channel.send(
            f"{message.author.mention} this might help.", embed=embed
        )

    async def process_requires_self_addition(self, message):
        """
        Look in a message and attempt to auto-help on
        instances where members send code IN a cog
        that doesnt contain self
        """
        event_requires_self_addition = self.event_requires_self_addition.search(
            message.content
        )
        command_requires_self_addition = self.command_requires_self_addition.search(
            message.content
        )

        if event_requires_self_addition is not None:
            # Event posted, check if it needs self
            to_use_regex = event_requires_self_addition
            msg = "an event"
        elif command_requires_self_addition is not None:
            # Command posted, check if it needs self
            to_use_regex = command_requires_self_addition
            msg = "a command"
        else:
            return

        args_group = to_use_regex.group(2)
        if args_group.startswith("self"):
            return

        initial_func = (
            to_use_regex.group(1) + to_use_regex.group(2) + to_use_regex.group(3)
        )

        args_group = f"self, {args_group}"

        final_func = to_use_regex.group(1) + args_group + to_use_regex.group(3)

        # We need to process this
        embed = nextcord.Embed(
            description=f"Looks like your defining {msg} in a class (Cog) without "
            "using `self` as the first variable. This will likely lead to issues and "
            "you should change it as per the following:"
            f"\n\n**Old**\n`{initial_func}`\n**New | Fixed**\n`{final_func}`",
            timestamp=message.created_at,
            color=0x26F7FD,
        )
        embed.set_author(name="Pyro Auto Helper", icon_url=message.guild.me.avatar.url)
        embed.set_footer(text="Believe this is incorrect? Let Skelmis know.")

        await message.channel.send(
            f"{message.author.mention} this might help.", embed=embed
        )

    def extract_code(self, message: nextcord.Message) -> List[str]:
        """Extracts all codeblocks to str"""
        content: List[str] = []
        current = []
        parsed_lst: List[str] = message.content.split("\n")

        is_codeblock = False
        for item in parsed_lst:
            # Only keep items with content from codeblocks
            if "```" in item:
                is_codeblock = not is_codeblock

                if not is_codeblock:
                    content.append("\n".join(current))
                    current = []

                continue

            if is_codeblock:
                current.append(item)

        return content

    @commands.command()
    @ensure_is_menudocs_guild()
    async def init(self, ctx):
        """Sends a helpful embed about how to fix import errors."""
        embed = nextcord.Embed(
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
        embed = nextcord.Embed(
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
    @ensure_is_menudocs_staff()
    @ensure_is_menudocs_guild()
    async def paste(
        self, ctx: commands.Context, messages: Greedy[nextcord.Message] = None
    ):
        """Given a message, create a pastebin for it"""
        if not messages:
            messages = [
                message
                async for message in ctx.channel.history(limit=2)
                if message.author != ctx.guild.me
            ]

            if len(messages) == 2 and messages[0].author.id != messages[1].author.id:
                # Make sure messages only come from the same person
                messages.pop(1)

        total_messages = len(messages)
        if total_messages > 2:
            return await ctx.send("I can only convert 1 or 2 messages to a paste")

        if total_messages == 1:
            code = self.extract_code(messages[0])
        else:
            code = self.extract_code(messages[0])
            code.extend(self.extract_code(messages[1]))

        # Ensure theres something to upload
        if not code:
            return await ctx.send("Couldn't extract anything to store")

        # Setup paste parts
        extracted_code = code[0]
        try:
            extracted_error = code[1]
        except IndexError:
            extracted_error = ""

        try:
            entry = await self.axew.async_create_paste(
                code=extracted_code,
                error=extracted_error,
                description=f"Extracted paste for {messages[0].author.display_name} in {ctx.guild.name}"
            )
        except BaseAxewException as e:
            return await ctx.send(str(e))

        mention_turnery = (
            f"{ctx.author.mention} and {messages[0].author.mention}"
            if ctx.author != messages[0].author
            else f"{ctx.author.mention}"
        )
        embed = nextcord.Embed(
            title="Find your paste here",
            url=entry.resolve_url(),
            description=f"[{entry.resolve_url()}]({entry.resolve_url()})",
            timestamp=ctx.message.created_at,
        )
        embed.set_footer(
            text="You can now delete the code and or error from your message"
        ),

        await ctx.send(f"Hey, {mention_turnery}", embed=embed)
        await ctx.message.delete()

    @commands.command(enabled=False)
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
