"""Tests for pyreostream.client.ReolinkClient."""

import asyncio
from collections.abc import AsyncGenerator

import pytest

from pyreostream.client import ReolinkClient
from pyreostream.exceptions import PyReoStreamConnectionError, PyReoStreamTimeoutError


@pytest.fixture(name="fake_server")
async def fake_server_fixture() -> AsyncGenerator[asyncio.Server, None]:
    """Start a bare TCP server standing in for a Reolink camera."""

    async def _handle(_reader: asyncio.StreamReader, _writer: asyncio.StreamWriter) -> None:
        pass

    server = await asyncio.start_server(_handle, "127.0.0.1", 0)
    async with server:
        yield server


def _server_port(server: asyncio.Server) -> int:
    port: int = server.sockets[0].getsockname()[1]
    return port


async def test_connect_reaches_authentication_stub(fake_server: asyncio.Server) -> None:
    """connect() opens the TCP socket then hits the (unimplemented) auth handshake."""
    client = ReolinkClient("127.0.0.1", username="user", password="pass", port=_server_port(fake_server))

    with pytest.raises(NotImplementedError):
        await client.connect()

    assert not client.connected


async def test_connect_connection_refused() -> None:
    """connect() wraps a refused connection in PyReoStreamConnectionError."""
    client = ReolinkClient("127.0.0.1", username="user", password="pass", port=1)

    with pytest.raises(PyReoStreamConnectionError):
        await client.connect()


async def test_connect_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """connect() wraps a connection timeout in PyReoStreamTimeoutError."""

    async def _hang(*_args: object, **_kwargs: object) -> None:
        await asyncio.sleep(3600)

    monkeypatch.setattr(asyncio, "open_connection", _hang)
    client = ReolinkClient("127.0.0.1", username="user", password="pass", request_timeout=0.01)

    with pytest.raises(PyReoStreamTimeoutError):
        await client.connect()


async def test_get_motion_not_implemented() -> None:
    """get_motion() raises NotImplementedError until Baichuan support lands."""
    client = ReolinkClient("127.0.0.1", username="user", password="pass")

    with pytest.raises(NotImplementedError):
        await client.get_motion()


async def test_read_frame_not_implemented() -> None:
    """read_frame() raises NotImplementedError until Baichuan support lands."""
    client = ReolinkClient("127.0.0.1", username="user", password="pass")

    with pytest.raises(NotImplementedError):
        await client.read_frame()


async def test_video_frames_yields_nothing_when_not_connected() -> None:
    """video_frames() yields nothing once the client is disconnected."""
    client = ReolinkClient("127.0.0.1", username="user", password="pass")

    frames = [frame async for frame in client.video_frames()]

    assert frames == []


async def test_close_when_never_connected() -> None:
    """close() is a no-op when the client never connected."""
    client = ReolinkClient("127.0.0.1", username="user", password="pass")

    await client.close()

    assert not client.connected


async def test_context_manager_closes_on_failed_connect(fake_server: asyncio.Server) -> None:
    """The async context manager leaves the client disconnected if connect() fails."""
    client = ReolinkClient("127.0.0.1", username="user", password="pass", port=_server_port(fake_server))

    with pytest.raises(NotImplementedError):
        async with client:
            pass

    assert not client.connected
