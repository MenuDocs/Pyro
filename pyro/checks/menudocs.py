from typing import TYPE_CHECKING

from nextcord.ext import commands

from pyro.checks import MENUDOCS_GUILD_IDS, COMBINED_ACCOUNTS
from pyro import MenuDocsOnly


if TYPE_CHECKING:
    from bot_base import BotContext


class MenuDocsCog(commands.Cog):
    @property
    def name(self) -> str:
        return self.__class__.__name__

    async def cog_check(self, ctx: "BotContext") -> bool:
        if (
            not ctx.guild
            or ctx.guild.id not in MENUDOCS_GUILD_IDS
            and ctx.author.id not in COMBINED_ACCOUNTS
        ):
            raise MenuDocsOnly(
                guild_id=ctx.guild.id,
                module=self.name.lower(),
                command_name=ctx.command.qualified_name,
                prefix=ctx.prefix,
            )

        return True
