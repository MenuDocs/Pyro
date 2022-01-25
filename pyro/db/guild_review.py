from typing import Optional

import nextcord


class GuildReview:
    def __init__(
        self,
        requester_id: int,
        name: str,
        purpose: str,
        specifics: str,
        guild_invite: str,
        text_channel_question: str,
        criticism_question: str,
        member_count: int,
        guild_type: str = "Misc",
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
        self.guild_type: str = guild_type
        self.member_count: int = member_count
        self.criticism_question: str = criticism_question
        self.channel_id: Optional[int] = channel_id
        self.text_channel_question: str = text_channel_question

    def to_dict(self):
        data = {
            "name": self.name,
            "purpose": self.purpose,
            "pending": self.pending,
            "specifics": self.specifics,
            "guild_type": self.guild_type,
            "guild_invite": self.guild_invite,
            "requester_id": self.requester_id,
            "member_count": self.member_count,
            "criticism_question": self.criticism_question,
            "text_channel_question": self.text_channel_question,
        }
        if self._id:
            data["_id"] = self._id

        if self.channel_id:
            data["channel_id"] = self.channel_id

        return data

    def as_embed(self, requester_name: str) -> nextcord.Embed:
        return nextcord.Embed(
            title=f"Guild review request for: `{requester_name}`",
            description=f"Guild name: `{self.name}`\n---\nPurpose: {self.purpose}\n---\n"
            f"Review specifics: {self.specifics}\n---\n"
            f"Review specific criticism: {self.criticism_question}\n---\n"
            f"Total text channels: {self.text_channel_question}\n---\n"
            f"Total member count: {self.member_count}\n---\n"
            f"Guild type: {self.guild_type}\n---\n"
            f"Discord invite: {self.guild_invite}",
        )
