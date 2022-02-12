import datetime
from typing import TYPE_CHECKING
from unittest.mock import Mock, AsyncMock

import pytest

if TYPE_CHECKING:
    from pyro import Pyro
    from tests.conftest import MockedTimedCache


def mock_message(content, author_id, guild_id, channel_id) -> Mock:
    """Mocks enough for autohelp to work"""
    mock = Mock()
    mock.content = content
    mock.guild.id = guild_id
    mock.author.id = author_id
    mock.created_at = datetime.datetime.utcnow()
    mock.author.roles = [Mock() for _ in range(5)]

    mock.channel = AsyncMock()
    mock.channel.id = channel_id

    return mock


@pytest.mark.asyncio
async def test_correct_process_commands(
    bot: "Pyro", mocked_cache: "MockedTimedCache"
) -> None:
    """Tests autohelp doesnt yell about process_commands"""
    bot.auto_help._help_cache = mocked_cache

    # Discord != python syntax
    code = """
    @bot.event\nasync def on_message(message):
        # mock data
        await bot.process_commands(message)
        """

    msg = mock_message(code, 1111, 2222, 3333)
    r_1 = await bot.auto_help.process_message(msg)
    assert r_1 is None
    assert msg.channel.send.call_count == 0

    code_2 = """
    @bot.event\nasync def on_message(message):
        if message.author:
            return
            
            
        """
    msg_2 = mock_message(code_2, 1111, 2222, 3333)
    r_2 = await bot.auto_help.process_message(msg_2)
    assert r_2 is not None
    assert len(r_2) == 1
    assert msg_2.channel.send.call_count == 1
