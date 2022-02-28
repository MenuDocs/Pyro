from typing import Union

import nextcord
from nextcord.ext import menus

from pyro.bot import Pyro


class TagsPageSource(menus.ListPageSource):
    def __init__(self, bot: Pyro, categories: list[str], prefix, per_page: int = 1):
        super().__init__(categories, per_page=per_page)
        self.bot = bot
        self.prefix: str = prefix

    async def format_page(self, menu, pages):
        embed = nextcord.Embed(title=f"Pyro tags - `{self.prefix}<tag>`")
        embed.description = "".join(pages)

        embed.set_footer(text=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
        return embed


class TagUsagePageSource(TagsPageSource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, per_page=10)
