from typing import Optional

from aiohttp import ClientSession
from bot_base import BotBase

from autohelp import AutoHelp
from db import PyroMongoManager


class Pyro(BotBase):
    def __init__(self, *args, **kwargs):
        # DB
        self.db: PyroMongoManager = PyroMongoManager(kwargs.pop("mongo_url"))
        self.session: Optional[ClientSession] = None

        super().__init__(*args, **kwargs)

        # Regex auto help
        self.auto_help: AutoHelp = AutoHelp(self)
