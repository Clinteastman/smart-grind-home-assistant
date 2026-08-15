# Smart Grind by Weight for Home Assistant

A native, local-push Home Assistant integration for the maintained [Smart Grind by Weight firmware](https://github.com/Clinteastman/smart-grind-by-weight). It discovers the grinder automatically on the local network and communicates directly with it—no cloud account and no MQTT broker.

> **Development status:** the integration and its matching firmware protocol are under active development. Do not install this repository on a production Home Assistant system until the first tagged release is published.

## What it provides

- Automatic discovery through the grinder's `_smartgrind._tcp` mDNS service
- Stable device identity from the ESP32 hardware ID, even if its IP address changes
- Live local state over WebSocket with automatic reconnect
- Weight, flow, progress, phase, target, and diagnostic sensors
- Grinding and motor-running binary sensors
- Single, Double, and Custom profile selection
- Weight/time mode selection on compatible firmware
- Start selected profile, manual start, stop, tare, and dismiss-result controls
- Recorder-friendly throttling of high-frequency scale data while phase and motor changes remain immediate
- Privacy-safe downloadable diagnostics with local addresses and hardware identity redacted
- A reconfigure flow for updating the grinder address while verifying it is the same device

All start and stop requests pass through the firmware's existing grind controller and safety checks. The integration does not control the motor GPIO directly.

## Requirements

- Home Assistant 2026.6 or newer
- [Smart Grind by Weight firmware v1.5.3](https://github.com/Clinteastman/smart-grind-by-weight/releases/tag/v1.5.3) or newer
- Home Assistant and the grinder on the same local network, with mDNS allowed between them

The basic live sensors and selected-profile start/stop controls can also communicate with firmware v1.5.2, but manual start, tare, correlated acknowledgements, and mode selection require the matching newer firmware.

## Installation

1. In HACS, open **Integrations**, choose **Custom repositories**, and add:
   `https://github.com/Clinteastman/smart-grind-home-assistant`
2. Select **Integration** as the category and download **Smart Grind by Weight**.
3. Restart Home Assistant.
4. Open **Settings → Devices & services**. The grinder should appear as a discovered device.
5. If discovery is blocked by network segmentation, choose **Add integration**, search for **Smart Grind by Weight**, and enter the IP address shown on the grinder's Wi-Fi page.

## Network behaviour

The integration reads device identity from `GET /api/v1/status`, reads profiles from `GET /api/v1/settings`, and subscribes to `ws://<grinder>/ws`. Commands carry a numeric request ID and are acknowledged by the firmware before Home Assistant reports success.

No Wi-Fi password or Home Assistant credential is sent to the grinder. Communication stays on the local network.

## Development

The canonical development checkout uses WSL2's Linux filesystem:

```bash
cd /home/cmossom/src/smart-grind-home-assistant
python3 -m venv .venv
.venv/bin/pip install '.[test]'
.venv/bin/ruff check .
.venv/bin/pytest
```

HACS validation and Hassfest run in GitHub Actions. See [AGENTS.md](AGENTS.md) for the firmware/integration boundary and safety rules.

An opt-in acceptance test loads the integration against a physical grinder
without sending any control command by default:

```bash
SMART_GRIND_LIVE_HOST=192.168.50.160 \
SMART_GRIND_LIVE_DEVICE_ID=684a8d858428 \
.venv/bin/pytest -m live tests/test_live_grinder.py
```

To verify two-way command acknowledgement as well, set
`SMART_GRIND_LIVE_COMMAND_TEST=1`. The test first proves the grinder is idle and
its motor is off, round-trips its existing profile and mode without changing
their effective values, then verifies safe `stop` and `dismiss` rejection paths.
It never starts the motor.

## Related projects and credits

- [Smart Grind by Weight maintained community firmware](https://github.com/Clinteastman/smart-grind-by-weight)
- [Original Smart Grind by Weight project by Jaap Pieroen](https://github.com/jaapp/smart-grind-by-weight)

This integration is independently implemented against the maintained firmware's documented local API.

## License

MIT
