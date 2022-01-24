from typing import TYPE_CHECKING

from nextcord.ext import commands

from pyro.checks import MENUDOCS_GUILD_IDS

if TYPE_CHECKING:
    from pyro import MenudocsOnly
    from bot_base import BotContext


class MenudocsCog(commands.Cog):
    @property
    def name(self) -> str:
        return self.__class__.__name__

    async def cog_check(self, ctx: "BotContext") -> bool:
        if not ctx.guild or ctx.guild.id not in MENUDOCS_GUILD_IDS:
            raise MenudocsOnly(guild_id=ctx.guild.id, module=self.name.lower())

        return True
