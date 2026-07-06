"""Tests for pyreostream.rtsp.RtspServer."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest

from pyreostream.exceptions import PyReoStreamError
from pyreostream.rtsp import RtspServer


def test_rejects_unsupported_codec() -> None:
    """RtspServer refuses to initialize with a codec it can't packetize."""
    with pytest.raises(PyReoStreamError):
        RtspServer(codec="mjpeg")


async def test_send_rtp_packet_not_implemented() -> None:
    """send_rtp_packet() raises NotImplementedError until GStreamer wiring lands."""
    server = RtspServer()

    with pytest.raises(NotImplementedError):
        await server.send_rtp_packet(b"frame")


async def test_relay_frames_not_implemented() -> None:
    """_relay_frames() raises NotImplementedError until the GStreamer pull lands."""
    server = RtspServer()
    server.enabled = True

    with pytest.raises(NotImplementedError):
        async for _ in server._relay_frames("rtsp://camera/h264Preview_01_main"):
            pass


async def test_relay_frames_yields_nothing_when_disabled() -> None:
    """_relay_frames() yields nothing once the server is disabled."""
    server = RtspServer()

    frames = [frame async for frame in server._relay_frames("rtsp://camera/h264Preview_01_main")]

    assert frames == []


async def test_start_forwards_frames_until_stopped() -> None:
    """start() forwards each relayed frame and stops once disabled."""
    server = RtspServer()
    server.send_rtp_packet = AsyncMock()  # type: ignore[method-assign]

    async def fake_relay_frames(_rtsp_url: str) -> AsyncIterator[bytes]:
        yield b"frame-1"
        await server.stop()
        yield b"frame-2"

    server._relay_frames = fake_relay_frames  # type: ignore[method-assign,assignment]

    await server.start("rtsp://camera/h264Preview_01_main")

    server.send_rtp_packet.assert_awaited_once_with(b"frame-1")
    assert not server.enabled


async def test_stop_before_start_is_a_noop() -> None:
    """stop() before start() simply leaves the server disabled."""
    server = RtspServer()

    await server.stop()

    assert not server.enabled
