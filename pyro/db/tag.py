from typing import Dict

import nextcord
from nextcord import Message, abc


class Tag:
    def __init__(
        self,
        name: str,
        content: str,
        creator_id: int,
        description: str,
        category: str,
        is_embed: bool = True,
        aliases: list[str] = None,
        _id=None,
    ):
        # _id is auto genned
        self._id = _id
        self.name: str = name
        self.content: str = content
        self.category: str = category
        self.is_embed: bool = is_embed
        self.creator_id: int = creator_id
        self.description: str = description

        if not aliases:
            aliases = []
        self.aliases: set = set(aliases)

    def __repr__(self):
        return (
            f"<Tag(name={repr(self.name)}, description={repr(self.description)}, "
            f"content={repr(self.content)}, creator_id={self.creator_id}, "
            f"category={repr(self.category)}, is_embed={self.is_embed})>"
        )

    def __str__(self):
        return f"<Tag(name={self.name}, description={self.description})>"

    def to_dict(self) -> Dict:
        data = {
            "name": self.name,
            "content": self.content,
            "category": self.category,
            "is_embed": self.is_embed,
            "aliases": list(self.aliases),
            "creator_id": self.creator_id,
            "description": self.description,
        }
        if self._id:
            data["_id"] = self._id

        return data

    async def send(self, target: abc.Messageable, invoked_with: str = None) -> Message:
        """Sends the given tag to the target"""
        if not invoked_with:
            invoked_with = self.name

        if self.is_embed:
            embed = nextcord.Embed(
                title=f"Tag: `{invoked_with}`", description=self.content
            )
            return await target.send(embed=embed)

        return await target.send(self.content)
