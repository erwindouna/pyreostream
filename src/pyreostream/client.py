"""Async client for Reolink cameras, backed by the reolink-aio library."""

import asyncio
import logging
from collections.abc import AsyncIterator
from types import TracebackType
from typing import Self

from reolink_aio.api import Host
from reolink_aio.exceptions import (
    ApiError,
    CredentialsInvalidError,
    LoginError,
    ReolinkConnectionError,
    ReolinkError,
    ReolinkTimeoutError,
)

from .const import DEFAULT_BAICHUAN_PORT
from .exceptions import (
    PyReoStreamAuthenticationError,
    PyReoStreamConnectionError,
    PyReoStreamTimeoutError,
)

_LOGGER = logging.getLogger(__name__)

_MOTION_CMD_ID = 33
_MOTION_CALLBACK_ID = "pyreostream-motion"


class ReolinkClient:
    """Async client for a Reolink camera.

    Wraps ``reolink_aio.api.Host`` for login (HTTP(S) and/or Baichuan) and
    keeps a Baichuan push subscription open so ``get_motion()``/``motion_changes()``
    reflect live camera state without polling. ``rtsp_url()`` resolves the
    camera's own RTSP stream for ``RtspServer`` to relay.
    """

    def __init__(
        self,
        host: str,
        *,
        username: str,
        password: str,
        port: int | None = None,
        bc_port: int = DEFAULT_BAICHUAN_PORT,
        channel: int = 0,
        request_timeout: float = 10.0,
    ) -> None:
        """Initialize the Reolink client."""
        self._channel = channel
        self._host = Host(host, username, password, port=port, bc_port=bc_port, timeout=int(request_timeout))
        self._connected = False
        self._motion_queue: asyncio.Queue[bool] = asyncio.Queue()

    @property
    def connected(self) -> bool:
        """Return whether the client is logged in to the camera."""
        return self._connected

    async def connect(self) -> None:
        """Log in to the camera and subscribe to motion push events."""
        try:
            await self._host.login()
            await self._host.baichuan.subscribe_events()
        except CredentialsInvalidError as err:
            raise PyReoStreamAuthenticationError(f"Invalid credentials for {self._host.host}") from err
        except (LoginError, ApiError) as err:
            raise PyReoStreamAuthenticationError(f"Could not log in to {self._host.host}: {err}") from err
        except ReolinkTimeoutError as err:
            raise PyReoStreamTimeoutError(f"Timed out connecting to {self._host.host}") from err
        except ReolinkConnectionError as err:
            raise PyReoStreamConnectionError(f"Could not connect to {self._host.host}") from err
        except ReolinkError as err:
            raise PyReoStreamConnectionError(str(err)) from err

        self._host.baichuan.register_callback(
            _MOTION_CALLBACK_ID,
            self._on_motion_push,
            cmd_id=_MOTION_CMD_ID,
            channel=self._channel,
        )
        self._connected = True

    def _on_motion_push(self) -> None:
        """Queue the latest motion state on a Baichuan push update."""
        self._motion_queue.put_nowait(self._host.motion_detected(self._channel))

    async def get_motion(self) -> bool:
        """Return whether the camera currently reports motion."""
        return self._host.motion_detected(self._channel)

    async def motion_changes(self) -> AsyncIterator[bool]:
        """Yield motion state changes as the camera pushes them."""
        while self.connected:
            yield await self._motion_queue.get()

    async def rtsp_url(self, *, stream: str = "main") -> str | None:
        """Return the camera's native RTSP stream URL for the given quality."""
        return await self._host.get_rtsp_stream_source(self._channel, stream=stream)

    async def close(self) -> None:
        """Unsubscribe from motion events and log out of the camera."""
        if not self._connected:
            return
        self._host.baichuan.unregister_callback(_MOTION_CALLBACK_ID)
        try:
            await self._host.baichuan.unsubscribe_events()
            await self._host.logout()
        finally:
            self._connected = False

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
