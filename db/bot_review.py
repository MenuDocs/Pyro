from typing import Optional


class BotReview:
    def __init__(
        self,
        requester_id: int,
        name: str,
        purpose: str,
        specifics: str,
        bot_invite: str,
        _id=None,
        pending: bool = True,
        channel_id: Optional[int] = None,
    ):
        self._id = _id
        self.name: str = name
        self.purpose: str = purpose
        self.specifics: str = specifics
        self.bot_invite: str = bot_invite
        self.pending: bool = pending
        self.requester_id: int = requester_id
        self.channel_id: Optional[int] = channel_id

    def to_dict(self):
        data = {
            "name": self.name,
            "purpose": self.purpose,
            "specifics": self.specifics,
            "bot_invite": self.bot_invite,
            "pending": self.pending,
            "requester_id": self.requester_id,
        }
        if self._id:
            data["_id"] = self._id

        if self.channel_id:
            data["channel_id"] = self.channel_id

        return data
