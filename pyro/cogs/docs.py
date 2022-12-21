import datetime
import io
import logging
import os
import re
import zlib

import aiohttp
import disnake
from disnake.ext import commands

log = logging.getLogger(__name__)


# Sphinx reader object because
# docs are written in sphinx.
class SphinxObjectFileReader:
    # Inspired by Sphinx's InventoryFileReader
    BUFSIZE = 16 * 1024

    def __init__(self, buffer):
        self.stream = io.BytesIO(buffer)

    def readline(self):
        return self.stream.readline().decode("utf-8")

    def skipline(self):
        self.stream.readline()

    def read_compressed_chunks(self):
        decompressor = zlib.decompressobj()
        while True:
            chunk = self.stream.read(self.BUFSIZE)
            if len(chunk) == 0:
                break
            yield decompressor.decompress(chunk)
        yield decompressor.flush()

    def read_compressed_lines(self):
        buf = b""
        for chunk in self.read_compressed_chunks():
            buf += chunk
            pos = buf.find(b"\n")
            while pos != -1:
                yield buf[:pos].decode("utf-8")
                buf = buf[pos + 1 :]
                pos = buf.find(b"\n")


class Docs(commands.Cog, name="Documentation"):
    def __init__(self, bot):
        self.bot = bot
        self.page_types = {
            "discord.py": "https://discordpy.readthedocs.io/en/latest",
            "nextcord": "https://nextcord.readthedocs.io/en/latest",
            "disnake": "https://docs.disnake.dev/en/latest",
            "levelling": "https://discord-ext-levelling.readthedocs.io/en/latest",
            "py": "https://docs.python.org/3",
            "python": "https://docs.python.org/3",
        }

    def finder(self, text, collection, *, key=None, lazy=True):
        suggestions = []
        text = str(text)
        pat = ".*?".join(map(re.escape, text))
        regex = re.compile(pat, flags=re.IGNORECASE)
        for item in collection:
            to_search = key(item) if key else item
            r = regex.search(to_search)
            if r:
                suggestions.append((len(r.group()), r.start(), item))

        def sort_key(tup):
            if key:
                return tup[0], tup[1], key(tup[2])
            return tup

        if lazy:
            return (z for _, _, z in sorted(suggestions, key=sort_key))
        else:
            return [z for _, _, z in sorted(suggestions, key=sort_key)]

    def parse_object_inv(self, stream, url):
        # key: URL
        result = {}

        # first line is version info
        inv_version = stream.readline().rstrip()

        if inv_version != "# Sphinx inventory version 2":
            raise RuntimeError("Invalid objects.inv file version.")

        # next line is "# Project: <name>"
        # then after that is "# Version: <version>"
        stream.readline().rstrip()[11:]
        stream.readline().rstrip()[11:]

        # next line says if it's a zlib header
        line = stream.readline()
        if "zlib" not in line:
            raise RuntimeError("Invalid objects.inv file, not z-lib compatible.")

        # This code mostly comes from the Sphinx repository.
        entry_regex = re.compile(r"(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)")
        for line in stream.read_compressed_lines():
            match = entry_regex.match(line.rstrip())
            if not match:
                continue

            name, directive, prio, location, dispname = match.groups()
            domain, _, subdirective = directive.partition(":")
            if directive == "py:module" and name in result:
                # From the Sphinx Repository:
                # due to a bug in 1.1 and below,
                # two inventory entries are created
                # for Python modules, and the first
                # one is correct
                continue

            # Most documentation pages have a label
            if directive == "std:doc":
                subdirective = "label"

            if location.endswith("$"):
                location = location[:-1] + name

            key = name if dispname == "-" else dispname
            prefix = f"{subdirective}:" if domain == "std" else ""

            result[f"{prefix}{key}"] = os.path.join(url, location)

        return result

    async def build_rtfm_lookup_table(self, page_types):
        cache = {}
        for key, page in page_types.items():
            async with aiohttp.ClientSession() as session:
                async with session.get(page + "/objects.inv") as resp:
                    if resp.status != 200:
                        raise RuntimeError(
                            "Cannot build rtfm lookup table, try again later."
                        )

                    stream = SphinxObjectFileReader(await resp.read())
                    cache[key] = self.parse_object_inv(stream, page)

        self._rtfm_cache = cache

    async def do_rtfm(self, interaction, key, obj):
        page_types = self.page_types
        key = key.lower()

        if obj is None:
            await interaction.send(page_types[key])
            return

        if not hasattr(self, "_rtfm_cache"):
            await self.build_rtfm_lookup_table(page_types)

        cache = list(self._rtfm_cache[key].items())

        self.matches = self.finder(obj, cache, key=lambda t: t[0], lazy=False)[:8]

        e = disnake.Embed(
            description=f"**Query:** `{obj}`\n\n",
            colour=0xCE2029,
            timestamp=datetime.datetime.now(),
        )
        if len(self.matches) == 0:
            return await interaction.send("Could not find anything. Sorry.")

        e.description += "\n".join(f"[`{key}`]({url})" for key, url in self.matches)
        e.set_footer(text=f"Requested by: {interaction.author.display_name}")
        await interaction.send(embed=e)

    @commands.Cog.listener()
    async def on_ready(self):
        log.info(f"{self.__class__.__name__} Cog has been loaded")

    @commands.command(name="docs")
    async def deprecated_docs(self, context: commands.Context):
        await context.send(
            "This command has been removed, please use the new slash command equivalent."
        )

    @commands.slash_command(guild_ids=[500525882226769931])
    async def docs(
        self,
        interaction: disnake.ApplicationCommandInteraction,
        query=commands.Param(description="The documentation query to lookup"),
        key=commands.Param(
            choices={
                "Nextcord": "nextcord",
                "Disnake": "disnake",
                "Discord.py": "discord.py",
                "Python": "python",
            },
            default="Nextcord",
            description="Which package to perform the lookup on",
        ),
    ):
        """Gives you a documentation link for an entity."""
        if key not in {"Nextcord", "Disnake", "Discord.py", "Python"}:
            return await interaction.send(
                ephemeral=True, content="Invalid documentation key provided."
            )

        await interaction.response.defer()
        await self.do_rtfm(interaction, key, query)


def setup(bot):
    bot.add_cog(Docs(bot))
