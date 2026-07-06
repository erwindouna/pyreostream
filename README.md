# pyreostream

[![GitHub Release][releases-shield]][releases]
[![Python Versions][python-versions-shield]][pypi]
![Project Stage][project-stage-shield]
![Project Maintenance][maintenance-shield]
[![License][license-shield]](LICENSE)

[![GitHub Activity][commits-shield]][commits-url]
[![PyPI Downloads][downloads-shield]][downloads-url]
[![GitHub Last Commit][last-commit-shield]][commits-url]
[![Open in Dev Containers][devcontainer-shield]][devcontainer]

[![Build Status][build-shield]][build-url]
[![Typing Status][typing-shield]][typing-url]
[![Code Coverage][codecov-shield]][codecov-url]

Bridge a Reolink camera's already-encoded H.264/H.265 video to RTSP/RTP and
publish its motion state to MQTT — without transcoding.

## About

pyreostream is an async Python bridge for Reolink cameras, focused on:

- Speaking the Reolink Baichuan protocol to pull encoded video frames and motion
  state (a Python port of what [Neolink](https://github.com/QuantumEntangledAndy/neolink)
  does in Rust)
- Serving those frames over RTSP/RTP without re-encoding, via GStreamer's `appsrc`
- Publishing motion on/off events to MQTT, gated so the RTSP stream only runs
  while motion is active

The library is under active development. The Baichuan protocol client and the
GStreamer RTSP server are currently stubs — see [Architecture](#architecture)
for what's implemented versus planned.

## Architecture

This is built in layers, each independently testable:

1. **Reolink protocol client** (`pyreostream.client.ReolinkClient`) — connects
   to the camera and speaks Baichuan to fetch motion state and encoded frames.
2. **Frame extraction** — `ReolinkClient.video_frames()` yields already-encoded
   H.264/H.265 frames; this project never encodes video itself.
3. **RTSP/RTP server** (`pyreostream.rtsp.RtspServer`) — packetizes those frames
   for RTSP clients using GStreamer, started/stopped on demand.
4. **MQTT motion publisher** (`pyreostream.mqtt.MotionPublisher`) — publishes
   retained motion on/off events.

## Installation

~~~bash
pip install pyreostream
~~~

Serving RTSP requires GStreamer with the `rtsp-server`, `app`, and
`h264parse`/`h265parse` plugins installed on the system (not installable via pip).

## Usage

~~~python
import asyncio

from pyreostream import MotionPublisher, ReolinkClient, RtspServer


async def main() -> None:
    async with ReolinkClient("192.168.2.10", username="admin", password="password") as camera:
        rtsp = RtspServer()
        motion_publisher = MotionPublisher("192.168.2.53")

        rtsp_task: asyncio.Task[None] | None = None

        while True:
            motion = await camera.get_motion()
            motion_publisher.publish(motion=motion)

            if motion and rtsp_task is None:
                rtsp_task = asyncio.create_task(rtsp.start(camera.video_frames()))

            if not motion and rtsp_task is not None:
                await rtsp.stop()
                rtsp_task.cancel()
                rtsp_task = None

            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())
~~~

See [`examples/example.py`](examples/example.py) for the full runnable version.

## Contributing

Contributions are welcome. Please open an issue or pull request.

For local development:

~~~bash
uv sync --all-groups && uv run pre-commit install
~~~

Run checks:

~~~bash
uv run pre-commit run --all-files
~~~

Run tests:

~~~bash
uv run pytest
~~~

## License

Apache License 2.0

Copyright 2026 Erwin Douna

<!-- MARKDOWN LINKS & IMAGES -->

[build-shield]: https://github.com/erwindouna/pyreostream/actions/workflows/tests.yaml/badge.svg
[build-url]: https://github.com/erwindouna/pyreostream/actions/workflows/tests.yaml
[codecov-shield]: https://codecov.io/gh/erwindouna/pyreostream/branch/main/graph/badge.svg
[codecov-url]: https://codecov.io/gh/erwindouna/pyreostream
[commits-shield]: https://img.shields.io/github/commit-activity/y/erwindouna/pyreostream.svg
[commits-url]: https://github.com/erwindouna/pyreostream/commits/main
[devcontainer-shield]: https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=visualstudiocode
[devcontainer]: https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/erwindouna/pyreostream
[downloads-shield]: https://img.shields.io/pypi/dm/pyreostream
[downloads-url]: https://pypistats.org/packages/pyreostream
[last-commit-shield]: https://img.shields.io/github/last-commit/erwindouna/pyreostream.svg
[license-shield]: https://img.shields.io/github/license/erwindouna/pyreostream.svg
[project-stage-shield]: https://img.shields.io/badge/project%20stage-experimental-yellow.svg
[maintenance-shield]: https://img.shields.io/maintenance/yes/2026.svg
[pypi]: https://pypi.org/project/pyreostream/
[python-versions-shield]: https://img.shields.io/pypi/pyversions/pyreostream
[releases-shield]: https://img.shields.io/github/release/erwindouna/pyreostream.svg
[releases]: https://github.com/erwindouna/pyreostream/releases
[typing-shield]: https://github.com/erwindouna/pyreostream/actions/workflows/typing.yaml/badge.svg
[typing-url]: https://github.com/erwindouna/pyreostream/actions/workflows/typing.yaml
