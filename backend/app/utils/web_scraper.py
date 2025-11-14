import httpx


def fetch_url(url: str, timeout: float = 10.0) -> str:
    """Fetch remote content via HTTP GET."""
    response = httpx.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text
