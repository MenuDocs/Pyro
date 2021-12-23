from bot_base.db import MongoManager
from bot_base.db.document import Document


class PyroMongoManager(MongoManager):
    def __init__(self, connection_url):
        super().__init__(connection_url=connection_url, database_name="pyro")

        self.quiz: Document = Document(self.db, "quiz")
        self.code: Document = Document(self.db, "code")
        self.config: Document = Document(self.db, "config")
        self.keywords: Document = Document(self.db, "keywords")
        self.starboard: Document = Document(self.db, "starboard")
        self.tictactoe: Document = Document(self.db, "tictactoe")
        self.quiz_answers: Document = Document(self.db, "quizAnswers")
