"""Watering countdown and paging logic. Pure functions; the date is always passed in."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import ceil

from .db import READY, Plant

PAGE_SIZE = 6
OVERDUE = "overdue"
DUE = "due"
OK = "ok"


def days_left(last_watered: date, interval_days: int, today: date) -> int:
    return interval_days - (today - last_watered).days


def status_of(days: int) -> str:
    if days < 0:
        return OVERDUE
    if days == 0:
        return DUE
    return OK


def plant_days_left(plant: Plant, today: date) -> int | None:
    if plant.data_status != READY or plant.interval_days is None:
        return None
    return days_left(plant.last_watered, plant.interval_days, today)


@dataclass(frozen=True)
class Page:
    number: int
    pages: int
    start: int
    end: int

    @property
    def has_prev(self) -> bool:
        return self.number > 1

    @property
    def has_next(self) -> bool:
        return self.number < self.pages


def paginate(total: int, page: int, per_page: int = PAGE_SIZE) -> Page:
    pages = max(1, ceil(total / per_page))
    number = min(max(page, 1), pages)
    start = (number - 1) * per_page
    return Page(number=number, pages=pages, start=start, end=min(start + per_page, total))
