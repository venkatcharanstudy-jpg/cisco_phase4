import asyncio


async def simulate_device_probe(device_id: str) -> dict[str, object]:
    await asyncio.sleep(0.2)
    return {"device_id": device_id, "reachable": True, "simulated": True}
