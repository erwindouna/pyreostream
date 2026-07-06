# pyreostream

Bridge a Reolink camera's already-encoded H.264/H.265 video to RTSP/RTP and
publish its motion state to MQTT — without transcoding.

## Architecture

This is built in layers, each independently testable:

1. **Reolink protocol client** ([`ReolinkClient`][pyreostream.client.ReolinkClient]) —
   connects to the camera and speaks Baichuan to fetch motion state and encoded frames.
2. **Frame extraction** — `ReolinkClient.video_frames()` yields already-encoded
   H.264/H.265 frames; this project never encodes video itself.
3. **RTSP/RTP server** ([`RtspServer`][pyreostream.rtsp.RtspServer]) — packetizes
   those frames for RTSP clients using GStreamer, started/stopped on demand.
4. **MQTT motion publisher** ([`MotionPublisher`][pyreostream.mqtt.MotionPublisher]) —
   publishes retained motion on/off events.

See the [API reference](api.md) for details, and
[`examples/example.py`](https://github.com/erwindouna/pyreostream/blob/main/examples/example.py)
for a runnable end-to-end example.
