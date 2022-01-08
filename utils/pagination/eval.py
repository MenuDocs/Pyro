from typing import Union

import nextcord
from nextcord.ext import menus

from bot import Pyro


class EvalPageSource(menus.ListPageSource):
    def __init__(
        self, bot: Pyro, code: str, author: Union[nextcord.User, nextcord.Member]
    ):
        super().__init__(
            [code[i : i + 2000] for i in range(0, len(code), 2000)], per_page=1
        )
        self.bot = bot
        self.author: Union[nextcord.User, nextcord.Member] = author

    async def format_page(self, menu, code):
        embed = nextcord.Embed(title=f"Eval for {self.author.name}")
        embed.description = f"```py{code}```"

        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed
