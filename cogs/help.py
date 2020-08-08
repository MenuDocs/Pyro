import logging

from discord.ext import buttons
from discord.ext import commands


class Help(commands.Cog, name="Help command"):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.cmds_per_page = 6

    def get_command_signature(
        self,
        command: commands.Command,
        ctx: commands.Context
    ):
        aliases = "|".join(command.aliases)
        cmd_invoke = (
            f"[{command.name}|{aliases}]"
            if command.aliases
            else command.name
        )

        full_invoke = command.qualified_name.replace(command.name, "")

        signature = (
            f"{ctx.prefix}{full_invoke}{cmd_invoke} {command.signature}"
        )
        return signature

    async def return_filtered_commands(self, walkable, ctx):
        filtered = []

        for c in walkable.walk_commands():
            try:
                if c.hidden:
                    # command is hidden
                    continue

                elif c.parent:
                    # Command is a subcommand
                    continue

                await c.can_run(ctx)
                filtered.append(c)
            except commands.CommandError:
                continue

        return filtered

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info("I'm ready!")

    @commands.command(
        name="help", aliases=["h", "commands"], description="The help command!"
    )
    async def help_command(self, ctx, *, entity=None):
        """
        Sends a paginated help command or help for
        an existing entity.
        """
        # Inspired by nekozilla
        if not entity:

            pages = []

            filtered_commands = await self.return_filtered_commands(
                self.bot,
                ctx
            )

            for i in range(0, len(filtered_commands), self.cmds_per_page):

                next_commands = filtered_commands[i: i + self.cmds_per_page]
                command_entry = ""

                for cmd in next_commands:

                    desc = cmd.short_doc or cmd.description
                    subcommand = (
                        'Has subcommands'
                        if hasattr(cmd, 'all_commands')
                        else ''
                    )

                    command_entry += (
                        f"• **__{cmd.name}__**\n{desc}\n    {subcommand}\n"
                    )

                pages.append(command_entry)

            await buttons.Paginator(
                title=self.bot.description,
                embed=True,
                colour=0xCE2029,
                entries=pages,
                length=1
            ).start(ctx)

        else:
            cog = self.bot.get_cog(entity)
            if cog:
                pages = []
                filtered_commands = await self.return_filtered_commands(
                    cog,
                    ctx
                )

                for i in range(0, len(filtered_commands), self.cmds_per_page):

                    command_entry = ""
                    next_commands = filtered_commands[
                        i: i + self.cmds_per_page
                    ]

                    for cmd in next_commands:

                        desc = cmd.short_doc or cmd.description
                        subcommand = (
                            'Has subcommands'
                            if hasattr(cmd, 'all_commands')
                            else ''
                        )

                        command_entry += (
                            f"• **__{cmd.name}__**\n{desc}\n    {subcommand}\n"
                        )

                pages.append(command_entry)

                await buttons.Paginator(
                    title=f"{cog.qualified_name}'s commands",
                    embed=True,
                    colour=0xCE2029,
                    entries=pages,
                    length=1
                ).start(ctx)

            else:
                command = self.bot.get_command(entity)
                if command:
                    pages = []
                    desc = command.short_doc or command.description
                    signature = self.get_command_signature(command, ctx)
                    command_entry = f"```{signature}```\n{desc}\n\n"

                    if hasattr(command, 'all_commands'):

                        command_list = list(command.all_commands.values())

                        for i in range(
                            0,
                            len(command_list),
                            self.cmds_per_page,
                        ):
                            next_commands = command_list[
                                i: i + self.cmds_per_page
                            ]

                            for cmd in next_commands:

                                signature = self.get_command_signature(
                                    cmd,
                                    ctx
                                )

                                desc = cmd.short_doc or cmd.description

                                command_entry += (
                                   f" • **__{cmd.name}__**\n```\n{signature}```\n{desc}\n"
                                )

                    pages.append(command_entry)

                    await buttons.Paginator(
                        title=f"{command.qualified_name}",
                        embed=True,
                        colour=0xCE2029,
                        entries=pages,
                        length=1
                    ).start(ctx)

                else:
                    await ctx.send("Entity not found.")


def setup(bot):
    bot.add_cog(Help(bot))
