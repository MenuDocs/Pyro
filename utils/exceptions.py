from pymongo.errors import PyMongoError


class IdNotFound(PyMongoError):
    """Raised when _id was not found in the database collection."""

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = self.__doc__

    def __str__(self):
        return self.message
