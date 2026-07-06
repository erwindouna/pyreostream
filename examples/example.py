"""Example: bridge a Reolink camera's stream to RTSP, gated by motion, with MQTT."""

import asyncio

from pyreostream import MotionPublisher, ReolinkClient, RtspServer


async def main() -> None:
    """Run the example."""
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
