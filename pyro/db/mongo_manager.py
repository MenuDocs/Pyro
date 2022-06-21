from bot_base.db import MongoManager
from alaric import Document

from pyro.db import GuildReview, BotReview, Tag


class PyroMongoManager(MongoManager):
    def __init__(self, connection_url):
        super().__init__(connection_url=connection_url, database_name="pyro")

        self.quiz: Document = Document(self.db, "quiz")
        self.code: Document = Document(self.db, "code")
        self.config: Document = Document(self.db, "config")
        self.starboard: Document = Document(self.db, "starboard")
        self.tictactoe: Document = Document(self.db, "tictactoe")
        self.quiz_answers: Document = Document(self.db, "quizAnswers")

        # Use the features
        self.bot_reviews: Document = Document(
            self.db, "bot_review", converter=BotReview
        )
        self.guild_reviews: Document = Document(
            self.db, "guild_reviews", converter=GuildReview
        )
        self.tags: Document = Document(self.db, "tags", converter=Tag)
