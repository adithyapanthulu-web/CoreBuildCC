
import urllib.request
import asyncio
HEALTHCHECK_URL = "http://127.0.0.1:8000/health"
HEALTHCHECK_INTERVAL_SECONDS = 600


def _ping_health_endpoint() -> None:
    try:
        with urllib.request.urlopen(HEALTHCHECK_URL, timeout=5) as response:
            response.read()
    except Exception:
        pass


async def _healthcheck_loop() -> None:
    while True:
        await asyncio.to_thread(_ping_health_endpoint)
        await asyncio.sleep(HEALTHCHECK_INTERVAL_SECONDS)