from nextcord import DiscordException
from nextcord.ext.commands import CheckFailure


class BasePyroException(DiscordException):
    """Base exception to inject docs into."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = self.__doc__

    def __str__(self):
        return self.message


class MenudocsOnly(CheckFailure):
    """This module can only be used a Menudocs guild."""

    def __init__(self, guild_id: int, module: str):
        self.guild_id: int = guild_id
        self.module: str = module
