# Changelog

## [0.1.1] - 2026-08-16

- Kept the last known grinder state available during brief WebSocket or Wi-Fi
  reconnects instead of flashing every entity unavailable.
- Marked entities unavailable normally when an interruption lasts beyond the
  10-second grace period, and published the recovered state immediately.
- Added focused tests for brief, sustained and recovered disconnects.

## [0.1.0] - 2026-08-16

- Added automatic `_smartgrind._tcp` discovery and manual IP/hostname setup.
- Added a resilient local-push WebSocket connection with stable device identity,
  bounded reconnect backoff and recorder-friendly live-value throttling.
- Added weight, flow, progress, phase, target and diagnostic sensors, plus
  grinding and motor-state binary sensors.
- Added profile and grind-mode selection, selected-profile start, manual start,
  stop, tare and dismiss-result buttons.
- Added correlated command acknowledgements, clear Home Assistant errors for
  firmware safety rejections and compatibility handling for older API v1
  acknowledgements.
- Added reconfiguration with device-identity verification and privacy-safe
  downloadable diagnostics.
- Added HACS, Hassfest, Ruff, unit and opt-in physical-device validation.

[0.1.1]: https://github.com/Clinteastman/smart-grind-home-assistant/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Clinteastman/smart-grind-home-assistant/releases/tag/v0.1.0
