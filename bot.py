import os
from typing import Optional

import nextcord
from aiohttp import ClientSession
from bot_base import BotBase

from autohelp import AutoHelp
from checks.basic import COMBINED_ACCOUNTS
from db import PyroMongoManager


class Pyro(BotBase):
    def __init__(self, *args, **kwargs):
        # DB
        self.db: PyroMongoManager = PyroMongoManager(kwargs.pop("mongo_url"))
        self.session: Optional[ClientSession] = None

        super().__init__(*args, **kwargs)

        # Regex auto help
        self.auto_help: AutoHelp = AutoHelp(self)

        self.is_debug_mode = bool(os.environ.get("IS_LOCAL", False))

    async def on_message(self, message: nextcord.Message) -> None:
        if self.is_debug_mode and message.author.id not in COMBINED_ACCOUNTS:
            # During dev only run commands from us so as to not impact the end user
            return None

        return await super().on_message(message)
