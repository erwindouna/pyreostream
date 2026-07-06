"""RTSP server that relays a Reolink camera's native RTSP stream via GStreamer."""

import logging
from collections.abc import AsyncIterator

from .const import DEFAULT_RTSP_PORT
from .exceptions import PyReoStreamError

_LOGGER = logging.getLogger(__name__)


class RtspServer:
    """Relay a Reolink camera's own RTSP stream through a local RTSP mount.

    This does not encode or decode video: it pulls the camera's already-encoded
    stream as an RTSP client and re-packetizes the same frames for clients
    connecting to this server. GStreamer (via PyGObject and gst-rtsp-server)
    owns both the client pull and the RTP/RTSP framing on the way back out, so
    this class only needs to push pulled buffers into a named ``appsrc``
    element. Relaying rather than handing out the camera's URL directly means
    playback can be gated, e.g. only pulling/serving while motion is active.
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

    async def start(self, rtsp_url: str) -> None:
        """Start relaying the camera's stream at ``rtsp_url`` until stopped."""
        self.enabled = True
        async for frame in self._relay_frames(rtsp_url):
            if not self.enabled:
                break
            await self.send_rtp_packet(frame)

    async def stop(self) -> None:
        """Stop serving RTSP."""
        self.enabled = False

    async def _relay_frames(self, rtsp_url: str) -> AsyncIterator[bytes]:
        """Yield encoded frames pulled from the camera's own RTSP stream at ``rtsp_url``."""
        while self.enabled:
            yield await self._pull_frame(rtsp_url)

    async def _pull_frame(self, rtsp_url: str) -> bytes:
        """Pull a single encoded frame from the camera's own RTSP stream at ``rtsp_url``.

        Not yet implemented — intended pipeline is a GStreamer client pull
        (``rtspsrc location=<rtsp_url> ! rtp{h264,h265}depay ! {h264,h265}parse
        ! appsink``), reusing the same GStreamer/PyGObject dependency this
        class already requires to serve RTSP.
        """
        raise NotImplementedError("GStreamer RTSP relay source is not yet implemented")

    async def send_rtp_packet(self, frame: bytes) -> None:
        """Push a single encoded frame into the GStreamer appsrc element.

        Not yet implemented — requires a running GstRtspServer media factory
        with a named ``source`` appsrc to push buffers into.
        """
        raise NotImplementedError("GStreamer appsrc push is not yet implemented")
