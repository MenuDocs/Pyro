from typing import Union

import nextcord
from nextcord.ext import menus

from pyro.bot import Pyro


class TagsPageSource(menus.ListPageSource):
    def __init__(self, bot: Pyro, categories: list[str]):
        super().__init__(categories, per_page=5)
        self.bot = bot

    async def format_page(self, menu, pages):
        embed = nextcord.Embed(title=f"Pyro tags")
        embed.description = "\n\n".join(pages)

        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed
