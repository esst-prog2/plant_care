from __future__ import annotations

import logging
from pathlib import Path

import httpx

from .providers.wikipedia import USER_AGENT

log = logging.getLogger("plant_care")

MAX_BYTES = 5 * 1024 * 1024
_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def store_photo(
    image: str | None,
    photos_dir: Path,
    plant_id: int,
    client: httpx.Client | None = None,
) -> str | None:
    """Return the web path of the plant's photo, downloading remote images to disk.

    Bundled images (paths starting with "/") are used as they are. Returns None when a
    remote image cannot be fetched, so the card falls back to the placeholder.
    """
    if not image:
        return None
    if image.startswith("/"):
        return image
    owns_client = client is None
    client = client or httpx.Client(
        timeout=10, follow_redirects=True, headers={"User-Agent": USER_AGENT}
    )
    try:
        response = client.get(image)
        response.raise_for_status()
        extension = _EXTENSIONS.get(response.headers.get("content-type", "").split(";")[0].strip())
        if extension is None or len(response.content) > MAX_BYTES:
            return None
        photos_dir.mkdir(parents=True, exist_ok=True)
        (photos_dir / f"{plant_id}{extension}").write_bytes(response.content)
        return f"/photos/{plant_id}{extension}"
    except (httpx.HTTPError, OSError) as exc:
        log.warning("Could not store photo for plant %s: %s", plant_id, exc)
        return None
    finally:
        if owns_client:
            client.close()
