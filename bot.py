from bot_base import BotBase

from db import PyroMongoManager


class Pyro(BotBase):
    def __init__(self, *args, **kwargs):
        # DB
        self.db: PyroMongoManager = PyroMongoManager(kwargs.pop("mongo_url"))

        super().__init__(*args, **kwargs)
