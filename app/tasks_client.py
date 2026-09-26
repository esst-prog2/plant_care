"""Talking to Google Tasks through the user's own Apps Script web app."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Protocol

import httpx

# httpx logs every request URL at INFO level, and the web app address must stay private.
logging.getLogger("httpx").setLevel(logging.WARNING)

MARKER_PREFIX = "plant_care:"
RECORDED_WORD = "recorded"
_MARKER = re.compile(rf"{MARKER_PREFIX}(\d+)")


class TasksError(Exception):
    """Google (or the internet) could not be reached, or refused the request."""


@dataclass(frozen=True)
class RemoteTask:
    id: str
    plant_id: int | None
    title: str
    due: date | None
    completed: datetime | None
    recorded: bool = False

    @property
    def is_completed(self) -> bool:
        return self.completed is not None


class TasksClient(Protocol):
    def list_tasks(self) -> list[RemoteTask]:
        """Every task in the plant_care list, open and completed."""

    def create_task(self, plant_id: int, title: str, due: date) -> RemoteTask: ...

    def update_task(self, task_id: str, title: str, due: date) -> None: ...

    def complete_task(self, task_id: str) -> None:
        """Complete a task on the app's behalf and mark it as recorded."""

    def delete_task(self, task_id: str) -> None: ...


def make_notes(plant_id: int, recorded: bool = False) -> str:
    return f"{MARKER_PREFIX}{plant_id}" + (f" {RECORDED_WORD}" if recorded else "")


def parse_notes(notes: str | None) -> tuple[int | None, bool]:
    match = _MARKER.search(notes or "")
    if not match:
        return None, False
    return int(match.group(1)), RECORDED_WORD in (notes or "").lower()


def _parse_due(value: str | None) -> date | None:
    return date.fromisoformat(value[:10]) if value else None


def _parse_completed(value: str | None) -> datetime | None:
    if not value:
        return None
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def _to_task(raw: dict) -> RemoteTask:
    plant_id, recorded = parse_notes(raw.get("notes"))
    completed = _parse_completed(raw.get("completed"))
    if raw.get("status") == "completed" and completed is None:
        completed = datetime.now(timezone.utc)
    return RemoteTask(
        id=str(raw["id"]),
        plant_id=plant_id,
        title=str(raw.get("title") or ""),
        due=_parse_due(raw.get("due")),
        completed=completed,
        recorded=recorded,
    )


class AppsScriptClient:
    """Calls the web app in google/Code.gs. Every call carries the shared secret."""

    def __init__(self, url: str, secret: str, client: httpx.Client | None = None, timeout: float = 30.0):
        self._url = url
        self._secret = secret
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=True)

    def _call(self, action: str, **payload) -> dict:
        try:
            response = self._client.post(
                self._url, json={"secret": self._secret, "action": action, **payload}
            )
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            # the web app address is private, and httpx puts it into its error messages
            raise TasksError(
                f"Google Tasks request failed: {str(exc).replace(self._url, '<script url>')}"
            ) from None
        if not isinstance(data, dict) or not data.get("ok"):
            error = data.get("error") if isinstance(data, dict) else "unexpected response"
            raise TasksError(f"Google Tasks refused the request: {error}")
        return data

    def list_tasks(self) -> list[RemoteTask]:
        return [_to_task(raw) for raw in self._call("list").get("tasks", [])]

    def create_task(self, plant_id: int, title: str, due: date) -> RemoteTask:
        data = self._call("create", title=title, due=due.isoformat(), notes=make_notes(plant_id))
        return _to_task(data["task"])

    def update_task(self, task_id: str, title: str, due: date) -> None:
        self._call("update", id=task_id, title=title, due=due.isoformat())

    def complete_task(self, task_id: str) -> None:
        self._call("complete", id=task_id, recordedWord=RECORDED_WORD)

    def delete_task(self, task_id: str) -> None:
        self._call("delete", id=task_id)
