import logging
import os
from pathlib import Path
from traceback import format_exception
from typing import Optional, TYPE_CHECKING

import disnake
from aiohttp import ClientSession
from bot_base import BotBase
from disnake.ext import commands
from disnake.ext.commands import CommandNotFound

from pyro import MenuDocsOnly
from pyro.autohelp import AutoHelp
from pyro.db import PyroMongoManager

if TYPE_CHECKING:
    from bot_base import BotContext
    from disnake.errors import DiscordException

log = logging.getLogger(__name__)


class Pyro(BotBase):
    def __init__(self, *args, **kwargs):
        self.db: PyroMongoManager = PyroMongoManager(kwargs.pop("mongo_url"))
        self.session: Optional[ClientSession] = None

        super().__init__(*args, **kwargs)

        # Regex auto help
        self.auto_help: AutoHelp = AutoHelp(self)

        self.is_debug_mode = bool(os.environ.get("IS_LOCAL", False))

    async def on_command_error(
        self, ctx: "BotContext", err: "DiscordException"
    ) -> None:
        err = getattr(err, "original", err)
        if isinstance(err, MenuDocsOnly):
            await ctx.send_basic_embed(
                f"I'm sorry, the command `{err.prefix}{err.command_name}` can only be used in MenuDocs guilds."
            )
        elif isinstance(err, CommandNotFound):
            log.debug(str(err))
            return

        elif isinstance(err, commands.ConversionError):
            await ctx.send(err)

        elif isinstance(err, commands.MissingRequiredArgument):
            await ctx.send(f"Missing required argument: `{err.param}`")

        elif isinstance(err, commands.BadArgument):
            await ctx.send(err)

        elif isinstance(err, commands.ArgumentParsingError):
            await ctx.send(err)

        elif isinstance(err, commands.PrivateMessageOnly):
            await ctx.send("This command can only be used in PMs.")

        elif isinstance(err, commands.NoPrivateMessage):
            await ctx.send("This command can only be used in Guilds.")

        elif isinstance(err, commands.MissingPermissions):
            perms = ", ".join(
                f"`{perm.replace('_', ' ').title()}`" for perm in err.missing_perms
            )

            await ctx.send(f"You're missing the permissions: {perms}")

        elif isinstance(err, commands.BotMissingPermissions):
            perms = ", ".join(
                f"`{perm.replace('_', ' ').title()}`" for perm in err.missing_perms
            )

            await ctx.send(f"I'm missing the permissions: {perms}")

        elif isinstance(err, commands.DisabledCommand):
            await ctx.send(f"`{ctx.command.qualified_name}` is currently disabled.")

        elif isinstance(err, disnake.HTTPException):
            await ctx.send(
                "An error occurred while I was trying to execute a task. Are you sure I have the correct permissions?"
            )

        elif isinstance(err, commands.MaxConcurrencyReached):
            await ctx.send(
                f"`{ctx.command.qualified_name}` can only be used {err.number} command at a time under {str(err.per)}"
            )

        elif isinstance(err, (commands.CheckFailure, commands.CheckAnyFailure)):
            await ctx.send("You do not have permission to run this command.")

        elif isinstance(err, commands.NotOwner):
            await ctx.send("Nope.")
            log.warning(
                "Member(id=%s, username=%s) attempted to run Command(name='%s')",
                ctx.author.id,
                ctx.author.display_name,
                ctx.command.qualified_name,
            )

        log.error("".join(format_exception(type(err), err, err.__traceback__)))

    async def load_cogs(self):
        count = 0
        extensions = Path("./pyro/cogs").rglob("*.py")
        for ext in extensions:
            _path = ".".join(ext.parts)
            self.load_extension(_path[:-3])
            count += 1

        log.debug("Loaded %s cogs", count)

    async def load(self):
        """An async entrypoint for the bot."""
        await self.load_cogs()

    async def graceful_shutdown(self) -> None:
        """Gracefully shutdown the bot."""
        log.info("Shutting down")
        await self.close()
