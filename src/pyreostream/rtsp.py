"""RTSP server that forwards pre-encoded frames via GStreamer."""

import logging
from collections.abc import AsyncIterator

from .const import DEFAULT_RTSP_PORT
from .exceptions import PyReoStreamError

_LOGGER = logging.getLogger(__name__)


class RtspServer:
    """Serve pre-encoded H.264/H.265 frames over RTSP using GStreamer.

    This does not encode video: it packetizes frames a camera has already
    encoded. GStreamer (via PyGObject and gst-rtsp-server) owns RTP/RTSP
    framing, so this class only needs to push buffers into a named
    ``appsrc`` element.
    """

    def __init__(self, *, port: int = DEFAULT_RTSP_PORT, mount_point: str = "/stream", codec: str = "h264") -> None:
        """Initialize the RTSP server.

        Args:
            port: TCP port the RTSP server listens on.
            mount_point: RTSP mount path clients connect to, e.g. ``/stream``.
            codec: Either ``"h264"`` or ``"h265"``.

        """
        if codec not in ("h264", "h265"):
            raise PyReoStreamError(f"Unsupported codec: {codec}")
        self._port = port
        self._mount_point = mount_point
        self._codec = codec
        self.enabled = False

    async def start(self, frame_source: AsyncIterator[bytes]) -> None:
        """Start serving RTSP and forward frames from ``frame_source`` until stopped."""
        self.enabled = True
        async for frame in frame_source:
            if not self.enabled:
                break
            await self.send_rtp_packet(frame)

    async def stop(self) -> None:
        """Stop serving RTSP."""
        self.enabled = False

    async def send_rtp_packet(self, frame: bytes) -> None:
        """Push a single encoded frame into the GStreamer appsrc element.

        Not yet implemented — requires a running GstRtspServer media factory
        with a named ``source`` appsrc to push buffers into.
        """
        raise NotImplementedError("GStreamer appsrc push is not yet implemented")
