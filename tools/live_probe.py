"""Read identity and one pushed state from a grinder without sending commands."""

from __future__ import annotations

import argparse
import asyncio
import contextlib

import aiohttp

from custom_components.smart_grind.client import SmartGrindClient
from custom_components.smart_grind.models import SmartGrindState


async def async_probe(host: str) -> None:
    """Run a non-mutating protocol probe."""
    timeout = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        client = SmartGrindClient(host, session)
        status = await client.async_get_status()
        settings = await client.async_get_settings()
        received = asyncio.Event()
        latest: SmartGrindState | None = None

        async def receive(state: SmartGrindState) -> None:
            nonlocal latest
            latest = state
            received.set()

        await client.async_connect()
        listener = asyncio.create_task(client.async_listen(receive))
        await asyncio.wait_for(received.wait(), timeout=5)
        if latest is None:
            raise RuntimeError("No live state received")
        print(
            f"device={status.device_id} firmware={status.firmware_version} "
            f"hardware={status.hardware_revision}"
        )
        print(
            f"profile={settings.current_profile} mode={settings.grind_mode} "
            f"phase={latest.phase} weight={latest.weight:.2f} "
            f"motor={latest.motor_running}"
        )
        listener.cancel()
        with contextlib.suppress(asyncio.CancelledError, Exception):
            await listener
        await client.async_disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", help="Grinder hostname or IP address")
    arguments = parser.parse_args()
    asyncio.run(async_probe(arguments.host))


if __name__ == "__main__":
    main()
