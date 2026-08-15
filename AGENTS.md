# Smart Grind Home Assistant development

- The canonical checkout is `/home/cmossom/src/smart-grind-home-assistant` in the `Ubuntu-24.04` WSL2 filesystem. Do not build or develop this repository through `/mnt/c`, OneDrive, or a Windows copy.
- The firmware checkout is `/home/cmossom/src/smart-grind-by-weight`.
- Keep the integration local-first: mDNS discovery, HTTP metadata and a resilient WebSocket push connection. Do not replace the native integration with MQTT discovery.
- All motor actions must use the firmware's controller-backed command API. Never expose direct GPIO or relay control.
- Keep device identity based on the ESP32 eFuse ID returned by `/api/v1/status`, never an IP address or editable hostname.
- Do not copy implementation code from GaggiMate or another Smart Grind fork. Independently implement the documented protocol using current Home Assistant patterns.
- Before publishing changes, run `ruff check .`, `pytest`, HACS validation, and Hassfest. Firmware protocol changes must also build both V1 and V2 targets.
- Never include Wi-Fi credentials, Home Assistant tokens, API keys, diagnostic logs containing secrets, or local network details in commits or fixtures.

