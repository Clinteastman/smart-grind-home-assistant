"""Constants for the Smart Grind by Weight integration."""

from typing import Final

DOMAIN: Final = "smart_grind"
DEFAULT_NAME: Final = "Smart Grind by Weight"
DEFAULT_PORT: Final = 80
CONNECTION_TIMEOUT_SECONDS: Final = 8.0

CONF_DEVICE_ID: Final = "device_id"

PLATFORMS: Final = ["binary_sensor", "button", "select", "sensor"]

WS_RECONNECT_MIN_SECONDS: Final = 1.0
WS_RECONNECT_MAX_SECONDS: Final = 30.0
WS_UNAVAILABLE_GRACE_SECONDS: Final = 10.0
COMMAND_TIMEOUT_SECONDS: Final = 5.0
