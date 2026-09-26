"""An in-memory stand-in for the Google Tasks list, with helpers that play the phone."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone

from app.tasks_client import RemoteTask, TasksError, make_notes


class FakeTasksClient:
    def __init__(self):
        self.tasks: dict[str, RemoteTask] = {}
        self.foreign: list[str] = []  # tasks in other lists; the client must never see them
        self.fail = False
        self.calls: list[tuple] = []
        self._next = 1

    def _check(self):
        if self.fail:
            raise TasksError("Google unreachable")

    def list_tasks(self):
        self._check()
        return list(self.tasks.values())

    def create_task(self, plant_id, title, due):
        self._check()
        self.calls.append(("create", plant_id, due))
        task = RemoteTask(f"t{self._next}", plant_id, title, due, None)
        self._next += 1
        self.tasks[task.id] = task
        return task

    def update_task(self, task_id, title, due):
        self._check()
        self.calls.append(("update", task_id, due))
        self.tasks[task_id] = replace(self.tasks[task_id], title=title, due=due)

    def complete_task(self, task_id):
        self._check()
        self.calls.append(("complete", task_id))
        self.tasks[task_id] = replace(
            self.tasks[task_id], completed=datetime.now(timezone.utc), recorded=True
        )

    def delete_task(self, task_id):
        self._check()
        self.calls.append(("delete", task_id))
        del self.tasks[task_id]

    # --- what the user does in the Google apps -------------------------------------
    def open_for(self, plant_id) -> list[RemoteTask]:
        return sorted(
            (t for t in self.tasks.values() if t.plant_id == plant_id and not t.is_completed),
            key=lambda t: t.due,
        )

    def dues_for(self, plant_id) -> list[date]:
        return [t.due for t in self.open_for(plant_id)]

    def tick(self, task_id, when: datetime):
        self.tasks[task_id] = replace(self.tasks[task_id], completed=when)

    def user_deletes(self, task_id):
        del self.tasks[task_id]

    def user_moves(self, task_id, due: date):
        self.tasks[task_id] = replace(self.tasks[task_id], due=due)

    def user_adds_stray(self, title="Buy soil", plant_id=None):
        task = RemoteTask(f"t{self._next}", plant_id, title, date(2026, 12, 1), None)
        self._next += 1
        self.tasks[task.id] = task
        return task

    def notes_of(self, plant_id):
        return make_notes(plant_id)


class FakeOnlineSource:
    """Stands in for Wikipedia: returns a fixed answer or fails like an unreachable service."""

    def __init__(self, info=None, fail=False):
        from app.providers.base import OnlineInfo

        self.info = info if info is not None else OnlineInfo()
        self.fail = fail
        self.asked: list[str] = []

    def lookup(self, title):
        from app.providers.base import ProviderError

        self.asked.append(title)
        if self.fail:
            raise ProviderError("offline")
        return self.info
