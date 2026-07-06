"""Example: bridge a Reolink camera's stream to RTSP, gated by motion, with MQTT."""

import asyncio

from pyreostream import MQTTPublisher, ReolinkClient, RtspServer


async def main() -> None:
    """Run the example."""
    async with ReolinkClient("192.168.2.10", username="admin", password="password") as camera:
        rtsp = RtspServer()
        mqtt_publisher = MQTTPublisher("192.168.2.1")

        rtsp_task: asyncio.Task[None] | None = None

        async for motion in camera.motion_changes():
            mqtt_publisher.publish("reolink/motion", "ON" if motion else "OFF")

            if motion and rtsp_task is None and (url := await camera.rtsp_url()) is not None:
                rtsp_task = asyncio.create_task(rtsp.start(url))

            if not motion and rtsp_task is not None:
                await rtsp.stop()
                rtsp_task.cancel()
                rtsp_task = None


if __name__ == "__main__":
    asyncio.run(main())
