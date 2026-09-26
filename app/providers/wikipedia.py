from __future__ import annotations

from urllib.parse import quote

import httpx

from .base import OnlineInfo, ProviderError

SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
# Wikimedia answers 403 to requests that do not say who is calling (robot policy).
USER_AGENT = "plant_care/1.0 (https://github.com/esst-prog2/plant_care; personal houseplant reminder project)"
MAX_ABOUT_CHARS = 600


def shorten(text: str, limit: int = MAX_ABOUT_CHARS) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = cut.rfind(". ")
    return cut[: end + 1] if end > limit // 2 else cut.rstrip() + "…"


class WikipediaSource:
    def __init__(self, client: httpx.Client | None = None, timeout: float = 5.0):
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=True)

    def lookup(self, title: str) -> OnlineInfo:
        try:
            response = self._client.get(
                SUMMARY_URL + quote(title, safe=""),
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            )
        except httpx.HTTPError as exc:
            raise ProviderError(f"Wikipedia request failed: {exc}") from exc
        if response.status_code == 404:
            return OnlineInfo()
        try:
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ProviderError(f"Wikipedia answered badly: {exc}") from exc
        if not isinstance(data, dict):
            raise ProviderError("Wikipedia returned an unexpected response")
        thumbnail = data.get("thumbnail") or {}
        page = (data.get("content_urls") or {}).get("desktop") or {}
        extract = data.get("extract")
        return OnlineInfo(
            image_url=thumbnail.get("source"),
            about=shorten(extract) if extract else None,
            page_url=page.get("page"),
        )
