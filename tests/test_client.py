"""Tests for pyreostream.client.ReolinkClient."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from reolink_aio.exceptions import (
    ApiError,
    CredentialsInvalidError,
    LoginError,
    ReolinkConnectionError,
    ReolinkTimeoutError,
)

from pyreostream.client import ReolinkClient
from pyreostream.exceptions import (
    PyReoStreamAuthenticationError,
    PyReoStreamConnectionError,
    PyReoStreamTimeoutError,
)


@pytest.fixture(name="mock_host")
def mock_host_fixture() -> Generator[MagicMock]:
    """Provide a stand-in for reolink_aio.api.Host, patched into pyreostream.client."""
    with patch("pyreostream.client.Host") as mock_host_cls:
        mock_host = mock_host_cls.return_value
        mock_host.host = "192.168.2.10"
        mock_host.login = AsyncMock()
        mock_host.logout = AsyncMock()
        mock_host.get_rtsp_stream_source = AsyncMock(return_value="rtsp://192.168.2.10/h264Preview_01_main")
        mock_host.motion_detected = MagicMock(return_value=False)
        mock_host.baichuan = MagicMock()
        mock_host.baichuan.subscribe_events = AsyncMock()
        mock_host.baichuan.unsubscribe_events = AsyncMock()
        yield mock_host


async def test_connect_logs_in_and_subscribes(mock_host: MagicMock) -> None:
    """connect() logs in, opens a Baichuan push subscription, and registers a motion callback."""
    client = ReolinkClient("192.168.2.10", username="user", password="pass")

    await client.connect()

    mock_host.login.assert_awaited_once()
    mock_host.baichuan.subscribe_events.assert_awaited_once()
    mock_host.baichuan.register_callback.assert_called_once()
    kwargs = mock_host.baichuan.register_callback.call_args.kwargs
    assert kwargs["cmd_id"] == 33
    assert kwargs["channel"] == 0
    assert client.connected


@pytest.mark.parametrize(
    ("raised", "expected"),
    [
        (CredentialsInvalidError("bad password"), PyReoStreamAuthenticationError),
        (LoginError("login failed"), PyReoStreamAuthenticationError),
        (ApiError("api error"), PyReoStreamAuthenticationError),
        (ReolinkTimeoutError("timed out"), PyReoStreamTimeoutError),
        (ReolinkConnectionError("refused"), PyReoStreamConnectionError),
    ],
)
async def test_connect_wraps_reolink_aio_errors(mock_host: MagicMock, raised: Exception, expected: type[Exception]) -> None:
    """connect() maps reolink-aio's exceptions onto pyreostream's own exception types."""
    mock_host.login.side_effect = raised
    client = ReolinkClient("192.168.2.10", username="user", password="pass")

    with pytest.raises(expected):
        await client.connect()

    assert not client.connected


async def test_get_motion_reads_from_host(mock_host: MagicMock) -> None:
    """get_motion() reflects the host's push-updated motion state."""
    client = ReolinkClient("192.168.2.10", username="user", password="pass")
    await client.connect()

    mock_host.motion_detected.return_value = True
    assert await client.get_motion() is True

    mock_host.motion_detected.return_value = False
    assert await client.get_motion() is False


async def test_motion_changes_yields_pushed_state(mock_host: MagicMock) -> None:
    """motion_changes() yields whatever the Baichuan push callback queues."""
    client = ReolinkClient("192.168.2.10", username="user", password="pass")
    await client.connect()

    mock_host.motion_detected.return_value = True
    on_motion_push = mock_host.baichuan.register_callback.call_args.args[1]
    on_motion_push()

    changes = client.motion_changes()
    assert await changes.__anext__() is True


async def test_rtsp_url_delegates_to_host(mock_host: MagicMock) -> None:
    """rtsp_url() resolves the camera's native RTSP stream via the host."""
    client = ReolinkClient("192.168.2.10", username="user", password="pass")

    url = await client.rtsp_url(stream="main")

    mock_host.get_rtsp_stream_source.assert_awaited_once_with(0, stream="main")
    assert url == "rtsp://192.168.2.10/h264Preview_01_main"


async def test_close_unsubscribes_and_logs_out(mock_host: MagicMock) -> None:
    """close() unregisters the motion callback, unsubscribes, and logs out."""
    client = ReolinkClient("192.168.2.10", username="user", password="pass")
    await client.connect()

    await client.close()

    mock_host.baichuan.unregister_callback.assert_called_once()
    mock_host.baichuan.unsubscribe_events.assert_awaited_once()
    mock_host.logout.assert_awaited_once()
    assert not client.connected


async def test_close_when_never_connected_is_noop(mock_host: MagicMock) -> None:
    """close() is a no-op when connect() was never called."""
    client = ReolinkClient("192.168.2.10", username="user", password="pass")

    await client.close()

    mock_host.logout.assert_not_called()
    assert not client.connected


async def test_context_manager_connects_and_closes(mock_host: MagicMock) -> None:
    """The async context manager connects on enter and closes on exit."""
    async with ReolinkClient("192.168.2.10", username="user", password="pass") as client:
        assert client.connected

    mock_host.logout.assert_awaited_once()


async def test_context_manager_leaves_disconnected_on_failed_connect(mock_host: MagicMock) -> None:
    """The async context manager leaves the client disconnected if connect() fails."""
    mock_host.login.side_effect = ReolinkConnectionError("refused")
    client = ReolinkClient("192.168.2.10", username="user", password="pass")

    with pytest.raises(PyReoStreamConnectionError):
        async with client:
            pass

    assert not client.connected
