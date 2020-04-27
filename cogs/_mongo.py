import logging

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

    async def find_by_id(self, id):
        """
        Returns the data found under `id`

        Params:
         -  id () : The id to search for

        Returns:
         - None if nothing is found
         - If somethings found, return that
        """
        return await self.db.find_one({"_id": id})

    async def find(self, id):
        """
        For simpler calls, points to self.find_by_id
        """
        return await self.find_by_id(id)

    async def delete_by_id(self, id):
        """
        Deletes all items found with _id: `id`

        Params:
         -  id () : The id to search for and delete
        """
        try:
            await self.db.delete_many({"_id": id})
        except Exception as e:
            self.logger.error(e)

    async def delete(self, id):
        """
        For simpler calls, points to self.delete_by_id
        """
        await self.delete_by_id(id)

    async def insert(self, dict):
        """
        Makes a new item in the document, if it already exists
        it will update that item instead

        This function parses an input Dictionary to get
        the relevant information needed to insert.
        Supports inserting when the document already exists

        Params:
         - dict (Dictionary) : The dict to insert
        """
        if await self.find_by_id(dict["_id"]):
            await self.update_by_id(dict)
        else:
            await self.db.insert_one(dict)

    async def update_by_id(self, dict):
        """
        For when a document already exists in the data
        and you want to update something in it

        This function parses an input Dictionary to get
        the relevant information needed to update.
        Supports updating when the document doesnt exist

        Params:
         - dict (Dictionary) : The dict to insert
        """
        if not await self.find_by_id(dict["_id"]):
            await self.insert(dict)
        else:
            id = dict["_id"]
            dict.pop("_id")
            await self.db.update_one({"_id": id}, {"$set": dict})

    async def update(self, dict):
        """
        For simpler calls, points to self.update_by_id
        """
        await self.update_by_id(dict)

    async def get_all(self):
        """
        Returns a list of all data in the document
        """
        data = []
        async for document in self.db.find({}):
            data.append(document)
        return data

    async def get_by_id(self, id):
        """
        This is essentially find_by_id so point to that
        """
        return await self.find_by_id(id)
