import collections
from typing import List, Dict, Optional

from pymongo.results import DeleteResult


class Document:
    _version = 4  # A flag for use during help

    def __init__(self, connection, document_name):
        self.db = connection[document_name]

    # <-- Pointer Methods -->
    async def find(self, data_id) -> Dict:
        return await self.find_by_id(data_id)

    async def delete(self, data_id) -> Optional[DeleteResult]:
        return await self.delete_by_id(data_id)

    async def update(self, data, *args, **kwargs) -> None:
        await self.update_by_id(data, *args, **kwargs)

    # <-- Actual Methods -->
    async def get_all(self, filter_dict=None, *args, **kwargs) -> List:
        filter_dict = filter_dict or {}

        return await self.db.find(filter_dict, *args, **kwargs).to_list(None)

    async def find_by_id(self, data_id) -> Dict:
        return await self.db.find_one({"_id": data_id})

    async def find_by_custom(self, filter_dict) -> Dict:
        self.__ensure_dict(filter_dict)

        return await self.db.find_one(filter_dict)

    async def find_many_by_custom(self, filter_dict) -> List[Dict]:
        self.__ensure_dict(filter_dict)

        return await self.db.find(filter_dict).to_list(None)

    async def delete_by_id(self, data_id) -> Optional[DeleteResult]:
        if await self.find_by_id(data_id) is None:
            return

        return await self.db.delete_many({"_id": data_id})

    async def delete_by_custom(self, filter_dict) -> Optional[List[DeleteResult]]:
        self.__ensure_dict(filter_dict)

        if await self.find_by_custom(filter_dict) is None:
            return

        return await self.db.delete_many(filter_dict)

    async def insert(self, data) -> None:
        self.__ensure_dict(data)

        await self.db.insert_one(data)

    async def upsert(self, data, option="set", *args, **kwargs) -> None:
        await self.update_by_id(data, option, upsert=True, *args, **kwargs)

    async def update_by_id(self, data, option="set", *args, **kwargs) -> None:
        self.__ensure_dict(data)
        self.__ensure_id(data)

        if await self.find_by_id(data["_id"]) is None:
            return await self.insert(data)

        data_id = data.pop("_id")
        await self.db.update_one(
            {"_id": data_id}, {f"${option}": data}, *args, **kwargs
        )

    async def upsert_custom(
        self, filter_dict, update_data, option="set", *args, **kwargs
    ) -> None:
        await self.update_by_custom(
            filter_dict, update_data, option, upsert=True, *args, **kwargs
        )

    async def update_by_custom(
        self, filter_dict, update_data, option="set", *args, **kwargs
    ) -> None:
        self.__ensure_dict(filter_dict)
        self.__ensure_dict(update_data)

        if not bool(await self.find_by_custom(filter_dict)):
            # Insert
            return await self.insert({**filter_dict, **update_data})

        # Update
        await self.db.update_one(
            filter_dict, {f"${option}": update_data}, *args, **kwargs
        )

    async def unset(self, data) -> None:
        self.__ensure_dict(data)
        self.__ensure_id(data)

        if await self.find_by_id(data["_id"]) is None:
            return

        data_id = data.pop("_id")
        await self.db.update_one({"_id": data_id}, {"$unset": data})

    async def increment(self, data_id, amount, field) -> None:
        if await self.find_by_id(data_id) is None:
            return

        await self.db.update_one({"_id": data_id}, {"$inc": {field: amount}})

    # <-- Private methods -->
    @staticmethod
    def __ensure_dict(data):
        assert isinstance(data, collections.abc.Mapping)  # noqa

    @staticmethod
    def __ensure_id(data):
        assert "_id" in data
