from __future__ import annotations

from dataclasses import dataclass

from .base import OnlineInfo, OnlineSource, PlantType, ProviderError
from .local_json import PREFIX as LOCAL_PREFIX
from .local_json import LocalProvider

SOURCE_ONLINE = "online"
SOURCE_LOCAL = "local"
SOURCE_FALLBACK = "local-fallback"


class CareDataUnavailable(Exception):
    """The selected plant type is not in the bundled list."""


@dataclass(frozen=True)
class CareResult:
    care: PlantType
    image_url: str | None
    about: str | None
    credit_url: str | None
    source: str


class CareDataService:
    """Care data from the bundled list; photo and description from an online source."""

    def __init__(self, local: LocalProvider, online: OnlineSource | None = None):
        self._local = local
        self._online = online

    def search(self, query: str) -> list[PlantType]:
        return self._local.search(query)

    def get(self, type_id: str, name: str) -> CareResult:
        if not type_id.startswith(LOCAL_PREFIX):
            raise CareDataUnavailable(f"No data available for {name!r}")
        try:
            care = self._local.get(type_id)
        except ProviderError as exc:
            raise CareDataUnavailable(str(exc)) from exc
        if self._online is None or not care.wiki_title:
            return CareResult(care, None, None, None, SOURCE_LOCAL)
        try:
            info: OnlineInfo = self._online.lookup(care.wiki_title)
        except ProviderError:
            return CareResult(care, None, None, None, SOURCE_FALLBACK)
        source = SOURCE_ONLINE if info.image_url or info.about else SOURCE_LOCAL
        return CareResult(care, info.image_url, info.about, info.page_url, source)
