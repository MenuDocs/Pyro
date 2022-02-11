import pytest
from bot_base.caches import TimedCache

from pyro import Pyro


@pytest.fixture(scope="session")
def bot() -> Pyro:
    return Pyro(command_prefix="py.", leave_db=True, mongo_url="Mocks")


@pytest.fixture()
def mocked_cache():
    class MockedTimedCache(TimedCache):
        def add_entry(
            self,
            key,
            value,
            *,
            ttl=None,
            override: bool = False,
        ) -> None:
            return None

        def delete_entry(self, key) -> None:
            return None

        def get_entry(self, key):
            return None

    return MockedTimedCache()
