from typing import Any


class UsgsClient:
    def __init__(self, url: str, timeout_seconds: float = 30) -> None:
        self.url = url
        self.timeout_seconds = timeout_seconds

    def fetch_latest(self) -> list[dict[str, Any]]:
        import httpx

        response = httpx.get(self.url, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        return payload.get("features", [])
