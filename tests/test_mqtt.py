"""Tests for pyreostream.mqtt.MotionPublisher."""

from unittest.mock import MagicMock, patch

from pyreostream.mqtt import MotionPublisher


@patch("pyreostream.mqtt.mqtt.Client")
def test_init_connects_and_starts_loop(mock_client_cls: MagicMock) -> None:
    """Constructing a MotionPublisher connects to the broker and starts its network loop."""
    mock_client = mock_client_cls.return_value

    MotionPublisher("broker.local", port=1883)

    mock_client.connect.assert_called_once_with("broker.local", 1883)
    mock_client.loop_start.assert_called_once()


@patch("pyreostream.mqtt.mqtt.Client")
def test_publish_sends_retained_on_off_message(mock_client_cls: MagicMock) -> None:
    """publish() sends a retained ON/OFF message on the configured topic."""
    mock_client = mock_client_cls.return_value
    publisher = MotionPublisher("broker.local", topic="reolink/argus/motion")

    publisher.publish(motion=True)
    mock_client.publish.assert_called_once_with("reolink/argus/motion", "ON", retain=True)

    publisher.publish(motion=False)
    mock_client.publish.assert_called_with("reolink/argus/motion", "OFF", retain=True)


@patch("pyreostream.mqtt.mqtt.Client")
def test_close_stops_loop_and_disconnects(mock_client_cls: MagicMock) -> None:
    """close() stops the network loop and disconnects from the broker."""
    mock_client = mock_client_cls.return_value
    publisher = MotionPublisher("broker.local")

    publisher.close()

    mock_client.loop_stop.assert_called_once()
    mock_client.disconnect.assert_called_once()
