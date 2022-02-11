from typing import Dict

from nextcord import abc


class Tag:
    def __init__(
        self,
        name: str,
        content: str,
        creator_id: int,
        description: str,
        category: str,
        is_embed: bool = True,
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

    def __repr__(self):
        return (
            f"<Tag(name={self.name}, description={repr(self.description)}, "
            f"content={repr(self.content)}, creator_id={self.creator_id}, "
            f"category={self.category}, is_embed={self.is_embed})>"
        )

    def __str__(self):
        return f"<Tag(name={self.name}, description={self.description})>"

    def to_dict(self) -> Dict:
        data = {
            "name": self.name,
            "content": self.content,
            "category": self.category,
            "is_embed": self.is_embed,
            "creator_id": self.creator_id,
            "description": self.description,
        }
        if self._id:
            data["_id"] = self._id

        return data

    async def send(self, target: abc.Messageable) -> None:
        """Sends the given tag to the target"""
        raise NotImplementedError
