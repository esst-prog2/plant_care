from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

DEFAULT_INTERVAL_DAYS = 7


@dataclass(frozen=True)
class PlantType:
    type_id: str
    name: str
    light: str | None = None
    interval_days: int | None = None
    wiki_title: str | None = None


@dataclass(frozen=True)
class OnlineInfo:
    """What the online source knows about a plant; every field may be missing."""

    image_url: str | None = None
    about: str | None = None
    page_url: str | None = None


class ProviderError(Exception):
    """The source could not answer (network error, timeout, refusal, bad response)."""


class OnlineSource(Protocol):
    def lookup(self, title: str) -> OnlineInfo:
        """Photo, description and article link for an article title; raises ProviderError."""
