"""MQTT motion-state publisher."""

import logging

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from .const import DEFAULT_MQTT_PORT

_LOGGER = logging.getLogger(__name__)


class MotionPublisher:
    """Publish camera motion state to MQTT."""

    def __init__(self, host: str, *, port: int = DEFAULT_MQTT_PORT, topic: str = "reolink/motion") -> None:
        """Connect to the MQTT broker and start its network loop in the background."""
        self._topic = topic
        self._client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
        self._client.connect(host, port)
        self._client.loop_start()

    def publish(self, *, motion: bool) -> None:
        """Publish the current motion state as a retained MQTT message."""
        self._client.publish(self._topic, "ON" if motion else "OFF", retain=True)

    def close(self) -> None:
        """Disconnect from the MQTT broker."""
        self._client.loop_stop()
        self._client.disconnect()
