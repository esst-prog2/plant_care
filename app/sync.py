"""Keep the plants and the Google Tasks list in agreement, in both directions."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import date, datetime, timedelta, tzinfo
from typing import Callable

from .db import READY, Database, Plant
from .tasks_client import RemoteTask, TasksClient

log = logging.getLogger("plant_care")

REMINDERS_PER_PLANT = 2


@dataclass
class SyncReport:
    pulled: int = 0
    created: int = 0
    updated: int = 0
    completed: int = 0
    deleted: int = 0

    def summary(self) -> str:
        return (
            f"{self.pulled} watering(s) read from Google, {self.created} to-do(s) created, "
            f"{self.updated} moved, {self.completed} completed, {self.deleted} deleted"
        )


def _local_date(moment: datetime, today: date, tz: tzinfo | None) -> date:
    day = moment.astimezone(tz).date()
    return min(day, today)


def _title(plant: Plant) -> str:
    return f"Water {plant.name}"


def reconcile(
    db: Database, client: TasksClient, today: date, tz: tzinfo | None = None
) -> SyncReport:
    """Raises TasksError if Google cannot be reached; whatever was done before stays done."""
    report = SyncReport()
    tasks = client.list_tasks()
    by_plant: dict[int | None, list[RemoteTask]] = {}
    for task in tasks:
        by_plant.setdefault(task.plant_id, []).append(task)

    known_ids = {p.id for p in db.list_plants()}
    ready = [p for p in db.list_plants() if p.data_status == READY and p.interval_days]

    for plant in ready:
        ticks = [
            t.completed
            for t in by_plant.get(plant.id, [])
            if t.completed is not None and not t.recorded
        ]
        if not ticks:
            continue
        watered_on = _local_date(max(ticks), today, tz)
        if watered_on > plant.last_watered:
            db.mark_watered_from_google(plant.id, watered_on)
            report.pulled += 1

    for plant in [db.get_plant(p.id) for p in ready]:
        if plant is None:
            continue
        open_tasks = sorted(
            (t for t in by_plant.get(plant.id, []) if not t.is_completed),
            key=lambda t: (t.due or date.max, t.id),
        )
        if (
            open_tasks
            and plant.synced_watered is not None
            and plant.last_watered > plant.synced_watered
        ):
            client.complete_task(open_tasks.pop(0).id)
            report.completed += 1

        title = _title(plant)
        for index in range(REMINDERS_PER_PLANT):
            due = plant.last_watered + timedelta(days=plant.interval_days * (index + 1))
            if index < len(open_tasks):
                task = open_tasks[index]
                if task.due != due or task.title != title:
                    client.update_task(task.id, title, due)
                    report.updated += 1
            else:
                client.create_task(plant.id, title, due)
                report.created += 1
        for extra in open_tasks[REMINDERS_PER_PLANT:]:
            client.delete_task(extra.id)
            report.deleted += 1
        db.mark_synced(plant.id, plant.last_watered)

    for task in tasks:
        if task.plant_id is None or task.plant_id not in known_ids:
            client.delete_task(task.id)
            report.deleted += 1
    return report


class Syncer:
    """Runs reconcile safely from several places: never overlaps, never raises."""

    def __init__(
        self,
        db: Database,
        client: TasksClient,
        clock: Callable[[], date],
        tz: tzinfo | None = None,
    ):
        self._db = db
        self._client = client
        self._clock = clock
        self._tz = tz
        self._lock = threading.Lock()
        self._again = False

    def run(self) -> SyncReport | None:
        if not self._lock.acquire(blocking=False):
            self._again = True
            return None
        report = None
        try:
            while True:
                self._again = False
                try:
                    report = reconcile(self._db, self._client, self._clock(), self._tz)
                    log.info("Google sync done: %s", report.summary())
                except Exception:
                    log.exception("Google sync failed; it will be retried on the next sync")
                    report = None
                if not self._again:
                    return report
        finally:
            self._lock.release()
