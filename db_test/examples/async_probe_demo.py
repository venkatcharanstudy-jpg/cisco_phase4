"""Compare sequential and concurrent simulated probes.

Run from the project root with: python -m examples.async_probe_demo
"""

import asyncio
import time

from app.services.probe import simulate_device_probe

SAMPLE_DEVICE_IDS = ["RTR-101", "SW-102", "FW-103"]


async def probe_sequentially(device_ids: list[str]) -> list[dict[str, object]]:
    return [await simulate_device_probe(device_id) for device_id in device_ids]


async def probe_concurrently(device_ids: list[str]) -> list[dict[str, object]]:
    return list(await asyncio.gather(*(simulate_device_probe(d) for d in device_ids)))


def run_timed(label: str, probe_all) -> None:
    start = time.perf_counter()
    results = asyncio.run(probe_all(SAMPLE_DEVICE_IDS))
    elapsed = time.perf_counter() - start
    print(f"{label}: {len(results)} results in {elapsed:.2f}s")
    for result in results:
        print(f"  {result}")


def main() -> None:
    run_timed("Sequential", probe_sequentially)
    run_timed("Concurrent", probe_concurrently)


if __name__ == "__main__":
    main()
