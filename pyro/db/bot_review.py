from typing import Optional

import disnake


class BotReview:
    def __init__(
        self,
        requester_id: int,
        name: str,
        purpose: str,
        specifics: str,
        bot_invite: str,
        criticism_question: str,
        bot_type: str = "Misc",
        _id=None,
        pending: bool = True,
        channel_id: Optional[int] = None,
        closing_summary: Optional[str] = None,
    ):
        self._id = _id
        self.name: str = name
        self.purpose: str = purpose
        self.pending: bool = pending
        self.specifics: str = specifics
        self.bot_invite: str = bot_invite
        self.requester_id: int = requester_id
        self.bot_type: str = bot_type
        self.criticism_question: str = criticism_question
        self.channel_id: Optional[int] = channel_id
        self.closing_summary: Optional[str] = closing_summary

    def to_dict(self):
        data = {
            "name": self.name,
            "purpose": self.purpose,
            "pending": self.pending,
            "specifics": self.specifics,
            "bot_type": self.bot_type,
            "bot_invite": self.bot_invite,
            "requester_id": self.requester_id,
            "closing_summary": self.closing_summary,
            "criticism_question": self.criticism_question,
        }
        if self._id:
            data["_id"] = self._id

        if self.channel_id:
            data["channel_id"] = self.channel_id

        return data

    def as_embed(self, requester_name: str) -> disnake.Embed:
        embed = disnake.Embed(
            title=f"Bot review request for: `{requester_name}`",
            description=f"Bot name: `{self.name}`\n---\nPurpose: {self.purpose}\n---\n"
            f"Review specifics: {self.specifics}\n---\n"
            f"Review specific criticism: {self.criticism_question}\n---\n"
            f"Bot type: {self.bot_type}\n---\n"
            f"Bot invite: {self.bot_invite}",
        )

        if self.closing_summary:
            embed.description += f"\n---\nClosing summary: {self.closing_summary}"

        return embed
