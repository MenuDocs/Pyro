import logging
import collections

from utils.exceptions import IdNotFound

"""
A helper file for using mongo db
Class document aims to make using mongo calls easy, saves
needing to know the syntax for it. Just pass in the db instance
on init and the document to create an instance on and boom
"""


class Document:
    def __init__(self, connection, document_name):
        """
        Our init function, sets up the conenction to the specified document

        Params:
         - connection (Mongo Connection) : Our database connection
         - documentName (str) : The document this instance should be
        """
        self.db = connection[document_name]
        self.logger = logging.getLogger(__name__)

    # <-- Pointer Methods -->
    async def update(self, dict, *args, **kwargs):
        """
        For simpler calls, points to self.update_by_id
        """
        await self.update_by_id(dict, *args, **kwargs)

    async def get_all(self, filter={}, *args, **kwargs):
        """
        Returns a list of all data in the document
        """
        return await self.db.find(filter, *args, **kwargs).to_list(None)

    async def get_by_id(self, id):
        """
        This is essentially find_by_id so point to that
        """
        return await self.find_by_id(id)

    async def find(self, id):
        """
        For simpler calls, points to self.find_by_id
        """
        return await self.find_by_id(id)

    async def delete(self, id):
        """
        For simpler calls, points to self.delete_by_id
        """
        await self.delete_by_id(id)

    # <-- Actual Methods -->
    async def find_by_id(self, id):
        """
        Returns the data found under `id`

        Params:
         -  id () : The id to search for

        Returns:
         - None if nothing is found
         - If somethings found, return that
        """
        data = await self.db.find_one({"_id": id})
        # Check if its none because
        # if not data: can raise on more then just None
        if not data:
            raise IdNotFound()
        return data

    async def find_by_custom(self, filter):
        """
        Returns data found with the custom filter rather then just id

        Params:
         - filter (dict) : The filter to search by
        """
        if not isinstance(filter, collections.abc.Mapping):
            raise TypeError("Expected Dictionary.")

        data = await self.db.find_one(filter)
        if not data:
            raise IdNotFound()
        return data

    async def delete_by_id(self, id):
        """
        Deletes all items found with _id: `id`

        Params:
         -  id () : The id to search for and delete
        """
        # Raise if the _id does not exist in database
        if not await self.find_by_id(id):
            return

        await self.db.delete_many({"_id": id})

    async def insert(self, dict):
        """
        insert something into the db

        Params:
        - dict (Dictionary) : The Dictionary to insert
        """
        # Check if its actually a Dictionary
        if not isinstance(dict, collections.abc.Mapping):
            raise TypeError("Expected Dictionary.")

        # Always use your own _id
        if not dict["_id"]:
            raise KeyError("_id not found in supplied dict.")

        await self.db.insert_one(dict)

    async def upsert(self, dict, option="set", *args, **kwargs):
        """
        Makes a new item in the document, if it already exists
        it will update that item instead

        This function parses an input Dictionary to get
        the relevant information needed to insert.
        Supports inserting when the document already exists

        Params:
         - dict (Dictionary) : The dict to insert
        """
        await self.update_by_id(dict, option, upsert=True, *args, **kwargs)

    async def update_by_id(self, dict, option="set", *args, **kwargs):
        """
        For when a document already exists in the data
        and you want to update something in it

        This function parses an input Dictionary to get
        the relevant information needed to update.

        Params:
         - dict (Dictionary) : The dict to insert
        """
        # Check if its actually a Dictionary
        if not isinstance(dict, collections.abc.Mapping):
            raise TypeError("Expected Dictionary.")

        # Always use your own _id
        if not dict["_id"]:
            raise KeyError("_id not found in supplied dict.")

        # Raise if the _id does not exist in database
        if not await self.find_by_id(dict["_id"]):
            pass

        id = dict["_id"]
        dict.pop("_id")
        await self.db.update_one({"_id": id}, {f"${option}": dict}, *args, **kwargs)

    async def unset(self, dict):
        """
        For when you want to remove a field from
        a pre-existing document in the collection

        This function parses an input Dictionary to get
        the relevant information needed to unset.

        Params:
         - dict (Dictionary) : Dictionary to parse for info
        """
        # Check if its actually a Dictionary
        if not isinstance(dict, collections.abc.Mapping):
            raise TypeError("Expected Dictionary.")

        # Always use your own _id
        if not dict["_id"]:
            raise KeyError("_id not found in supplied dict.")

        # Raise if the _id does not exist in database
        await self.find_by_id(dict["_id"])

        id = dict["_id"]
        dict.pop("_id")
        await self.db.update_one({"_id": id}, {"$unset": dict})

    async def increment(self, id, amount, field):
        """
        Increment a given `field` by `amount`

        Params:
        - id () : The id to search for
        - amount (int) : Amount to increment by
        - field () : field to increment
        """
        # Raise if the _id does not exist in database
        await self.find_by_id(id)

        self.db.update_one({"_id": id}, {"$inc": {field: amount}})

    # <-- Private methods -->
    async def __get_raw(self, id):
        """
        An internal private method used to eval certain checks
        within other methods which require the actual data
        """
        return await self.db.find_one({"_id": id})
