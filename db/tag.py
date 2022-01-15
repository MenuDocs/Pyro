from typing import Dict

from nextcord import abc


class Tag:
    def __init__(
        self,
        name: str,
        content: str,
        description: str,
        is_embed: bool = True,
        _id=None,
    ):
        # _id is auto genned
        self._id = _id
        self.name: str = name
        self.content: str = content
        self.is_embed: bool = is_embed
        self.description: str = description

    def to_dict(self) -> Dict:
        data = {
            "name": self.name,
            "content": self.content,
            "description": self.description,
        }
        if self._id:
            data["_id"] = self._id

        return data

    async def send(self, target: abc.Messageable) -> None:
        """Sends the given tag to the target"""
        raise NotImplementedError
