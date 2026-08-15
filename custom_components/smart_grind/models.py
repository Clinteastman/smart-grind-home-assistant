"""Typed models for the Smart Grind local API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class SmartGrindError(Exception):
    """Base exception for Smart Grind communication errors."""


class SmartGrindConnectionError(SmartGrindError):
    """Raised when the grinder cannot be reached."""


class SmartGrindProtocolError(SmartGrindError):
    """Raised when the grinder returns an invalid message."""


class SmartGrindCommandError(SmartGrindError):
    """Raised when the grinder rejects a command."""


@dataclass(frozen=True, slots=True)
class SmartGrindDeviceStatus:
    """Static and slowly changing device status."""

    device_id: str
    model: str
    hardware_revision: str
    firmware_version: str
    firmware_build: int
    firmware_commit: str
    hostname: str
    ip_address: str
    protocol: int
    commands: frozenset[str]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> SmartGrindDeviceStatus:
        """Create status from an API payload."""
        try:
            device = payload["device"]
            firmware = payload["firmware"]
            network = payload["network"]
            capabilities = payload.get("capabilities", {})
            return cls(
                device_id=str(device["id"]),
                model=str(device["model"]),
                hardware_revision=str(device["hardware_revision"]),
                firmware_version=str(firmware["version"]),
                firmware_build=int(firmware["build"]),
                firmware_commit=str(firmware.get("commit", "")),
                hostname=str(network.get("hostname", "smartgrind")),
                ip_address=str(network.get("ip", "")),
                protocol=int(capabilities.get("protocol", 1)),
                commands=frozenset(str(value) for value in capabilities.get("commands", ())),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SmartGrindProtocolError("Invalid device status response") from exc


@dataclass(frozen=True, slots=True)
class SmartGrindProfile:
    """One grinder dose profile."""

    profile_id: int
    name: str
    weight: float
    time: float


@dataclass(frozen=True, slots=True)
class SmartGrindSettings:
    """Settings needed by Home Assistant entities."""

    current_profile: int
    grind_mode: str
    profiles: tuple[SmartGrindProfile, ...]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> SmartGrindSettings:
        """Create settings from an API payload."""
        try:
            profiles = tuple(
                SmartGrindProfile(
                    profile_id=int(profile["id"]),
                    name=str(profile["name"]).title(),
                    weight=float(profile["weight"]),
                    time=float(profile["time"]),
                )
                for profile in payload["profiles"]
            )
            mode = str(payload["grind_mode"])
            if mode not in {"weight", "time"}:
                raise ValueError("unsupported grind mode")
            return cls(
                current_profile=int(payload["current_profile"]),
                grind_mode=mode,
                profiles=profiles,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SmartGrindProtocolError("Invalid settings response") from exc


@dataclass(frozen=True, slots=True)
class SmartGrindState:
    """Live grinder state received over WebSocket."""

    sequence: int
    timestamp_ms: int
    active: bool
    phase: str
    grind_mode: str
    profile: int
    progress: int
    target_weight: float
    target_time_ms: int
    weight: float
    flow: float
    motor_running: bool
    free_heap: int

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> SmartGrindState:
        """Create live state from a WebSocket payload."""
        try:
            grind = payload["grind"]
            scale = payload["scale"]
            return cls(
                sequence=int(payload["seq"]),
                timestamp_ms=int(payload["timestamp_ms"]),
                active=bool(grind["active"]),
                phase=str(grind["phase"]).lower(),
                grind_mode=str(grind["mode"]),
                profile=int(grind["profile"]),
                progress=int(grind["progress"]),
                target_weight=float(grind["target_weight"]),
                target_time_ms=int(grind["target_time_ms"]),
                weight=float(scale["weight"]),
                flow=float(scale["flow"]),
                motor_running=bool(payload["motor"]["running"]),
                free_heap=int(payload["system"]["free_heap"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SmartGrindProtocolError("Invalid live state message") from exc
