from typing import Optional


class GuildReview:
    def __init__(
        self,
        requester_id: int,
        name: str,
        purpose: str,
        specifics: str,
        guild_invite: str,
        _id=None,
        pending: bool = True,
        channel_id: Optional[int] = None,
    ):
        self._id = _id
        self.name: str = name
        self.purpose: str = purpose
        self.pending: bool = pending
        self.specifics: str = specifics
        self.guild_invite: str = guild_invite
        self.requester_id: int = requester_id
        self.channel_id: Optional[int] = channel_id

    def to_dict(self):
        data = {
            "name": self.name,
            "purpose": self.purpose,
            "pending": self.pending,
            "specifics": self.specifics,
            "guild_invite": self.guild_invite,
            "requester_id": self.requester_id,
        }
        if self._id:
            data["_id"] = self._id

        if self.channel_id:
            data["channel_id"] = self.channel_id

        return data
