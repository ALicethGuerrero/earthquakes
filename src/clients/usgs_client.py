from typing import Any

import httpx


class UsgsClient:
    def __init__(
        self,
        url: str,
        timeout_seconds: float = 30.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.url = url
        self.timeout_seconds = timeout_seconds
        self._owned_client = client is None
        self._client = client or httpx.Client(timeout=httpx.Timeout(timeout_seconds))

    def fetch_latest(self) -> list[dict[str, Any]]:
        response = self._client.get(self.url)
        response.raise_for_status()
        payload = response.json()
        return payload.get("features", [])

    def close(self) -> None:
        if self._owned_client:
            self._client.close()

    def __enter__(self) -> "UsgsClient":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
