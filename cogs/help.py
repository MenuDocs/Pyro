import discord
from discord.ext import commands
import os
import random
import re
import math
import logging


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("I'm ready!")

    @commands.command(
        name="help", aliases=["h", "commands"], description="The help command!"
    )
    async def help_command(self, ctx, cog="1"):
        """
        The help command can either show a list of 4 cogs per page
        or a specific cog hence the checks
        """
        help_embed = discord.Embed(
            title="Help Command!", color=random.choice(self.bot.color_list)
        )
        help_embed.set_thumbnail(url=self.bot.user.avatar_url)
        cogs = [c for c in self.bot.cogs.keys()]
        totalPages = math.ceil(len(cogs) / 4)

        if re.search("\d", str(cog)):  # Match any numbers
            cog = int(cog)
            # Send a page of help commands
            if cog > totalPages or cog < 1:
                await ctx.send(
                    f"Invalid page number: `{cog}`. Please pick from {totalPages} pages.\nAlternatively, simply run `help` to see page one or type `help [category]` to see that categories help command!"
                )
                return

            help_embed.set_footer(
                text=f"<> - Required & [] - Optional | Page {cog} of {totalPages}"
            )

            neededCogs = []
            for i in range(4):
                x = i + (int(cog) - 1) * 4
                try:
                    neededCogs.append(cogs[x])
                except IndexError:
                    pass

            for cog in neededCogs:
                # Get a list of commands for each cog and put on embed
                commandList = ""
                for comm in self.bot.get_cog(cog).walk_commands():
                    if comm.hidden:
                        continue
                    commandList += f"**{comm.name}** - *{comm.description}*\n"
                commandList += "\n"

                # Add the cog's details to the embed.
                help_embed.add_field(name=cog, value=commandList, inline=False)

        elif re.search("[a-zA-Z]", str(cog)):  # Match any letters
            lowerCogs = [c.lower() for c in cogs]
            if cog.lower() in lowerCogs:
                help_embed.set_footer(
                    text=f"<> - Required & [] - Optional | Cog {(lowerCogs.index(cog.lower())+1)} of {len(lowerCogs)}"
                )
                # Get a list of all commands in the specified cog
                helpText = ""
                # Add details of each command to the help text
                # Command Name
                # Description
                # Useable by command caller
                # [Aliases]
                #
                # Format
                for command in self.bot.get_cog(cogs[lowerCogs.index(cog.lower())]).walk_commands():
                    if command.hidden:
                        continue

                    helpText += (
                        f"```{command.name}```\n" f"**{command.description}**\n\n"
                    )

                    # Also add aliases, if there are any
                    if len(command.aliases) > 0:
                        helpText += (
                            f'**Aliases :** `{"`, `".join(command.aliases)}`\n\n'
                        )
                    else:
                        # Add a newline character to keep it pretty
                        # That IS the whole purpose of custom help
                        helpText += "\n"

                    helpText += f"**Useable by {ctx.author.name}:** `{await command.can_run(ctx)}`\n\n"

                    # Finally the format
                    data = await self.bot.config.find(ctx.guild.id)
                    if not data or "prefix" not in data:
                        prefix = "-"
                    else:
                        prefix = data["prefix"]
                    helpText += f'**Format :** `{prefix}{command.name} {command.usage if command.usage is not None else ""}`\n\n\n\n'  # `@{self.bot.user.name}#{self.bot.user.discriminator}'
                help_embed.description = helpText
            else:
                # Notify the user of invalid cog and finish the command
                await ctx.send(
                    f"Invalid argument: `{cog}`. Please pick from {totalPages} pages.\nAlternatively, simply run `help` to see page one or type `help [category]` to see that categories help command!"
                )
                return

        else:  # Fallback for if nothing works
            await ctx.send(
                f"Invalid argument: `{cog}`. Please pick from {totalPages} pages.\nAlternatively, simply run `help` to see page one or type `help [category]` to see that categories help command!"
            )
            return
        await ctx.send(embed=help_embed)


def setup(bot):
    bot.add_cog(Help(bot))
