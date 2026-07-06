"""MQTT publisher."""

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from .const import DEFAULT_MQTT_PORT


class MQTTPublisher:
    """Publish states to MQTT."""

    def __init__(self, host: str, username: str | None = None, password: str | None = None, *, port: int = DEFAULT_MQTT_PORT) -> None:
        """Connect to the MQTT broker and start its network loop in the background."""
        self._client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
        if username and password:
            self._client.username_pw_set(username, password)
        self._client.connect(host, port)
        self._client.loop_start()

    def publish(self, topic: str, payload: str, *, retain: bool = True) -> None:
        """Publish a message to the given topic."""
        self._client.publish(topic, payload, retain=retain)

    def close(self) -> None:
        """Disconnect from the MQTT broker."""
        self._client.loop_stop()
        self._client.disconnect()
