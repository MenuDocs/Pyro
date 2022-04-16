from typing import Optional, Union

import nextcord
from nextcord.ext import menus


class PyroPag(menus.ButtonMenuPages):
    def __init__(
        self,
        author: Optional[Union[nextcord.Member, nextcord.User]] = None,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.author = author

    async def interaction_check(self, inter: nextcord.Interaction) -> bool:
        return inter.user.id == self.author.id if self.author is not None else True
