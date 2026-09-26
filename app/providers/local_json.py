from __future__ import annotations

import json
from pathlib import Path

from .base import PlantType, ProviderError

PREFIX = "local:"


class LocalProvider:
    def __init__(self, path: Path | str):
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        self._plants = [
            PlantType(
                type_id=PREFIX + item["id"],
                name=item["name"],
                light=item.get("light"),
                interval_days=item["watering_days"],
                wiki_title=item.get("wikipedia"),
            )
            for item in raw
        ]

    def search(self, query: str) -> list[PlantType]:
        needle = query.strip().casefold()
        if not needle:
            return []
        return [p for p in self._plants if needle in p.name.casefold()]

    def get(self, type_id: str) -> PlantType:
        for plant in self._plants:
            if plant.type_id == type_id:
                return plant
        raise ProviderError(f"Unknown plant type {type_id!r}")

    def all(self) -> list[PlantType]:
        return list(self._plants)
