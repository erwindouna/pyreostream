"""Tests for pyreostream.mqtt.MQTTPublisher."""

from unittest.mock import MagicMock, patch

from pyreostream.mqtt import MQTTPublisher


@patch("pyreostream.mqtt.mqtt.Client")
def test_init_connects_and_starts_loop(mock_client_cls: MagicMock) -> None:
    """Constructing an MQTTPublisher connects to the broker and starts its network loop."""
    mock_client = mock_client_cls.return_value

    MQTTPublisher("broker.local", port=1883)

    mock_client.connect.assert_called_once_with("broker.local", 1883)
    mock_client.loop_start.assert_called_once()


@patch("pyreostream.mqtt.mqtt.Client")
def test_publish_sends_message_to_topic(mock_client_cls: MagicMock) -> None:
    """publish() sends the given payload to the given topic, retained by default."""
    mock_client = mock_client_cls.return_value
    publisher = MQTTPublisher("broker.local")

    publisher.publish("reolink/argus/motion", "ON")
    mock_client.publish.assert_called_once_with("reolink/argus/motion", "ON", retain=True)

    publisher.publish("reolink/argus/motion", "OFF", retain=False)
    mock_client.publish.assert_called_with("reolink/argus/motion", "OFF", retain=False)


@patch("pyreostream.mqtt.mqtt.Client")
def test_close_stops_loop_and_disconnects(mock_client_cls: MagicMock) -> None:
    """close() stops the network loop and disconnects from the broker."""
    mock_client = mock_client_cls.return_value
    publisher = MQTTPublisher("broker.local")

    publisher.close()

    mock_client.loop_stop.assert_called_once()
    mock_client.disconnect.assert_called_once()
