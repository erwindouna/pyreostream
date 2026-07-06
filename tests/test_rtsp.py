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


async def test_start_forwards_frames_until_stopped() -> None:
    """start() forwards each frame from the source and stops once disabled."""
    server = RtspServer()
    server.send_rtp_packet = AsyncMock()  # type: ignore[method-assign]

    async def source() -> AsyncIterator[bytes]:
        yield b"frame-1"
        await server.stop()
        yield b"frame-2"

    await server.start(source())

    server.send_rtp_packet.assert_awaited_once_with(b"frame-1")
    assert not server.enabled


async def test_stop_before_start_is_a_noop() -> None:
    """stop() before start() simply leaves the server disabled."""
    server = RtspServer()

    await server.stop()

    assert not server.enabled
