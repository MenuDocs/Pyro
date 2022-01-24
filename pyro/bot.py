import os
from typing import Optional, TYPE_CHECKING

from aiohttp import ClientSession
from bot_base import BotBase

from pyro import MenuDocsOnly
from pyro.autohelp import AutoHelp
from pyro.db import PyroMongoManager

if TYPE_CHECKING:
    from bot_base import BotContext
    from nextcord.errors import DiscordException


class Pyro(BotBase):
    def __init__(self, *args, **kwargs):
        # DB
        self.db: PyroMongoManager = PyroMongoManager(kwargs.pop("mongo_url"))
        self.session: Optional[ClientSession] = None

        super().__init__(*args, **kwargs)

        # Regex auto help
        self.auto_help: AutoHelp = AutoHelp(self)

        self.is_debug_mode = bool(os.environ.get("IS_LOCAL", False))

    async def on_command_error(
        self, ctx: "BotContext", error: "DiscordException"
    ) -> None:
        if isinstance(error, MenuDocsOnly):
            await ctx.send_basic_embed(
                f"I'm sorry, the command `{error.prefix}{error.command_name}` can only be used in MenuDocs guilds."
            )

        await super().on_command_error(ctx, error)
