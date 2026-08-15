"""Tests for Smart Grind API models."""

import pytest

from custom_components.smart_grind.models import (
    SmartGrindDeviceStatus,
    SmartGrindProtocolError,
    SmartGrindSettings,
    SmartGrindState,
)


def test_parse_status_with_capabilities() -> None:
    status = SmartGrindDeviceStatus.from_payload(
        {
            "device": {
                "id": "684a8d858428",
                "model": "ESP32-S3-Touch-AMOLED-1.64",
                "hardware_revision": "v2",
            },
            "firmware": {"version": "1.5.3", "build": 7, "commit": "abc123"},
            "network": {"hostname": "smartgrind", "ip": "192.0.2.10"},
            "capabilities": {
                "protocol": 1,
                "commands": ["start", "tare", "select_profile"],
            },
        }
    )

    assert status.device_id == "684a8d858428"
    assert status.hardware_revision == "v2"
    assert status.commands == frozenset({"start", "tare", "select_profile"})


def test_parse_settings() -> None:
    settings = SmartGrindSettings.from_payload(
        {
            "current_profile": 1,
            "grind_mode": "weight",
            "profiles": [
                {"id": 0, "name": "SINGLE", "weight": 9.0, "time": 5.0},
                {"id": 1, "name": "DOUBLE", "weight": 18.0, "time": 10.0},
                {"id": 2, "name": "CUSTOM", "weight": 21.5, "time": 12.0},
            ],
        }
    )

    assert settings.current_profile == 1
    assert settings.profiles[1].name == "Double"
    assert settings.profiles[2].weight == 21.5


def test_parse_live_state() -> None:
    state = SmartGrindState.from_payload(
        {
            "seq": 11790,
            "timestamp_ms": 1192735,
            "grind": {
                "active": False,
                "phase": "IDLE",
                "mode": "weight",
                "profile": 1,
                "progress": 0,
                "target_weight": 18.0,
                "target_time_ms": 10000,
            },
            "scale": {"weight": -0.05, "flow": 0.16},
            "motor": {"running": False},
            "system": {"free_heap": 109188},
        }
    )

    assert state.phase == "idle"
    assert state.weight == -0.05
    assert state.motor_running is False


def test_reject_invalid_payload() -> None:
    with pytest.raises(SmartGrindProtocolError):
        SmartGrindState.from_payload({"seq": 1})
