from typing import Union

import nextcord
from nextcord.ext import menus

from pyro.bot import Pyro


class TicTacToePageSource(menus.ListPageSource):
    def __init__(
        self,
        bot: Pyro,
        stat_type,
        pages,
    ):
        super().__init__(pages, per_page=1)
        self.bot = bot
        self.stat_type = stat_type

    async def format_page(self, menu, page):
        embed = nextcord.Embed(title=f"TicTacToe leaderboard for `{self.stat_type}`")
        embed.description = page

        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed
