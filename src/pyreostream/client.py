"""Async client for the Reolink Baichuan camera protocol."""

import asyncio
import logging
from collections.abc import AsyncIterator
from types import TracebackType
from typing import Self

from .const import DEFAULT_BAICHUAN_PORT
from .exceptions import PyReoStreamConnectionError, PyReoStreamTimeoutError

_LOGGER = logging.getLogger(__name__)


class ReolinkClient:
    """Async client for a Reolink camera's Baichuan protocol.

    The Baichuan wire protocol is undocumented; Neolink (Rust) is the
    reference implementation this client is intended to port. Until that
    port lands, authentication, motion polling, and frame reads raise
    ``NotImplementedError``.
    """

    def __init__(
        self,
        host: str,
        *,
        username: str,
        password: str,
        port: int = DEFAULT_BAICHUAN_PORT,
        request_timeout: float = 10.0,
    ) -> None:
        """Initialize the Reolink client."""
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._request_timeout = request_timeout
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    @property
    def connected(self) -> bool:
        """Return whether the TCP connection to the camera is open."""
        return self._writer is not None and not self._writer.is_closing()

    async def connect(self) -> None:
        """Open the TCP connection and authenticate with the camera."""
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=self._request_timeout,
            )
        except TimeoutError as err:
            raise PyReoStreamTimeoutError(f"Timed out connecting to {self._host}:{self._port}") from err
        except OSError as err:
            raise PyReoStreamConnectionError(f"Could not connect to {self._host}:{self._port}") from err

        try:
            await self._authenticate()
        except Exception:
            await self.close()
            raise

    async def _authenticate(self) -> None:
        """Perform the Baichuan login handshake.

        Not yet implemented — requires porting Neolink's Baichuan login and
        AES-CBC encryption logic (keyed off the camera's nonce).
        """
        raise NotImplementedError("Baichuan authentication is not yet implemented")

    async def get_motion(self) -> bool:
        """Return whether the camera currently reports motion.

        Not yet implemented — requires the Baichuan motion-state message.
        """
        raise NotImplementedError("Baichuan motion polling is not yet implemented")

    async def read_frame(self) -> bytes:
        """Read a single encoded H.264/H.265 frame from the camera.

        Not yet implemented — requires parsing Baichuan's video payload
        framing (Neolink's ``bcmedia`` module is the reference).
        """
        raise NotImplementedError("Baichuan video framing is not yet implemented")

    async def video_frames(self) -> AsyncIterator[bytes]:
        """Yield encoded H.264/H.265 frames from the camera as they arrive."""
        while self.connected:
            yield await self.read_frame()

    async def close(self) -> None:
        """Close the TCP connection to the camera."""
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
            self._reader = None

    async def __aenter__(self) -> Self:
        """Async enter: connect to the camera."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Async exit: close the connection."""
        await self.close()
