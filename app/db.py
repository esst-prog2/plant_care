"""The only module that talks to the database."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import date
from pathlib import Path

LOADING = "loading"
READY = "ready"
FAILED = "failed"


@dataclass(frozen=True)
class Group:
    id: int
    name: str


@dataclass(frozen=True)
class Plant:
    id: int
    type_id: str
    name: str
    photo: str | None
    light: str | None
    interval_days: int | None
    date_added: date
    last_watered: date
    data_status: str
    data_source: str | None
    sync_pending: bool
    synced_watered: date | None
    about: str | None
    photo_credit: str | None
    toxicity: str | None
    humidity: str | None
    propagation: str | None
    photo_is_custom: bool
    group_id: int | None


_SCHEMA = """
CREATE TABLE IF NOT EXISTS plants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_id TEXT NOT NULL,
    name TEXT NOT NULL,
    photo TEXT,
    light TEXT,
    interval_days INTEGER,
    date_added TEXT NOT NULL,
    last_watered TEXT NOT NULL,
    data_status TEXT NOT NULL,
    data_source TEXT,
    sync_pending INTEGER NOT NULL DEFAULT 1,
    synced_watered TEXT,
    about TEXT,
    photo_credit TEXT
);
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

ALL_GROUP_NAME_KEY = "all_group_name"

_MIGRATIONS = {
    "sync_pending": "ALTER TABLE plants ADD COLUMN sync_pending INTEGER NOT NULL DEFAULT 1",
    "synced_watered": "ALTER TABLE plants ADD COLUMN synced_watered TEXT",
    "about": "ALTER TABLE plants ADD COLUMN about TEXT",
    "photo_credit": "ALTER TABLE plants ADD COLUMN photo_credit TEXT",
    "toxicity": "ALTER TABLE plants ADD COLUMN toxicity TEXT",
    "humidity": "ALTER TABLE plants ADD COLUMN humidity TEXT",
    "propagation": "ALTER TABLE plants ADD COLUMN propagation TEXT",
    "photo_is_custom": "ALTER TABLE plants ADD COLUMN photo_is_custom INTEGER",
    "group_id": "ALTER TABLE plants ADD COLUMN group_id INTEGER",
}


def _to_plant(row: sqlite3.Row) -> Plant:
    synced = row["synced_watered"]
    return Plant(
        id=row["id"],
        type_id=row["type_id"],
        name=row["name"],
        photo=row["photo"],
        light=row["light"],
        interval_days=row["interval_days"],
        date_added=date.fromisoformat(row["date_added"]),
        last_watered=date.fromisoformat(row["last_watered"]),
        data_status=row["data_status"],
        data_source=row["data_source"],
        sync_pending=bool(row["sync_pending"]),
        synced_watered=date.fromisoformat(synced) if synced else None,
        about=row["about"],
        photo_credit=row["photo_credit"],
        toxicity=row["toxicity"],
        humidity=row["humidity"],
        propagation=row["propagation"],
        photo_is_custom=bool(row["photo_is_custom"]),
        group_id=row["group_id"],
    )


def _to_group(row: sqlite3.Row) -> Group:
    return Group(id=row["id"], name=row["name"])


class Database:
    def __init__(self, path: Path | str):
        self.path = str(path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.executescript(_SCHEMA)
            columns = {row["name"] for row in conn.execute("PRAGMA table_info(plants)")}
            for column, statement in _MIGRATIONS.items():
                if column not in columns:
                    conn.execute(statement)

    def add_plant(self, type_id: str, name: str, today: date, group_id: int | None = None) -> Plant:
        with closing(self._connect()) as conn, conn:
            cur = conn.execute(
                "INSERT INTO plants (type_id, name, date_added, last_watered, data_status, group_id)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (type_id, name, today.isoformat(), today.isoformat(), LOADING, group_id),
            )
            plant_id = cur.lastrowid
        return self.get_plant(plant_id)

    def complete_plant(
        self,
        plant_id: int,
        photo: str | None,
        light: str | None,
        interval_days: int,
        data_source: str,
        about: str | None = None,
        photo_credit: str | None = None,
        toxicity: str | None = None,
        humidity: str | None = None,
        propagation: str | None = None,
    ) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "UPDATE plants SET photo=?, light=?, interval_days=?, data_source=?,"
                " data_status=?, about=?, photo_credit=?, toxicity=?, humidity=?,"
                " propagation=?, sync_pending=1 WHERE id=?",
                (
                    photo, light, interval_days, data_source, READY, about, photo_credit,
                    toxicity, humidity, propagation, plant_id,
                ),
            )

    def fail_plant(self, plant_id: int) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute("UPDATE plants SET data_status=? WHERE id=?", (FAILED, plant_id))

    def list_plants(self, group_id: int | None = None) -> list[Plant]:
        with closing(self._connect()) as conn:
            if group_id is None:
                rows = conn.execute(
                    "SELECT * FROM plants WHERE data_status != ? ORDER BY id", (FAILED,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM plants WHERE data_status != ? AND group_id = ? ORDER BY id",
                    (FAILED, group_id),
                ).fetchall()
        return [_to_plant(r) for r in rows]

    def count_plants(self) -> int:
        with closing(self._connect()) as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM plants WHERE data_status != ?", (FAILED,)
            ).fetchone()[0]

    def get_plant(self, plant_id: int) -> Plant | None:
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT * FROM plants WHERE id=?", (plant_id,)).fetchone()
        return _to_plant(row) if row else None

    def delete_plant(self, plant_id: int) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute("DELETE FROM plants WHERE id=?", (plant_id,))

    def create_group(self, name: str) -> Group:
        with closing(self._connect()) as conn, conn:
            cur = conn.execute("INSERT INTO groups (name) VALUES (?)", (name,))
            group_id = cur.lastrowid
        return self.get_group(group_id)

    def list_groups(self) -> list[Group]:
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT * FROM groups ORDER BY id").fetchall()
        return [_to_group(r) for r in rows]

    def get_group(self, group_id: int) -> Group | None:
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT * FROM groups WHERE id=?", (group_id,)).fetchone()
        return _to_group(row) if row else None

    def rename_group(self, group_id: int, name: str) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute("UPDATE groups SET name=? WHERE id=?", (name, group_id))

    def delete_group(self, group_id: int) -> None:
        """Unassigns the group's plants (they fall back to "All") before deleting it."""
        with closing(self._connect()) as conn, conn:
            conn.execute("UPDATE plants SET group_id=NULL WHERE group_id=?", (group_id,))
            conn.execute("DELETE FROM groups WHERE id=?", (group_id,))

    def set_plant_group(self, plant_id: int, group_id: int | None) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute("UPDATE plants SET group_id=? WHERE id=?", (group_id, plant_id))

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?)"
                " ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def set_custom_photo(self, plant_id: int, photo: str) -> None:
        """A user-uploaded photo, which replaces whatever photo was shown before."""
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "UPDATE plants SET photo=?, photo_is_custom=1 WHERE id=?", (photo, plant_id)
            )

    def mark_watered(self, plant_id: int, today: date) -> None:
        """A watering recorded in the app."""
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "UPDATE plants SET last_watered=?, sync_pending=1 WHERE id=?",
                (today.isoformat(), plant_id),
            )

    def mark_watered_from_google(self, plant_id: int, day: date) -> None:
        """A watering that Google already knows about (a to-do ticked off on the phone)."""
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "UPDATE plants SET last_watered=?, synced_watered=?, sync_pending=1 WHERE id=?",
                (day.isoformat(), day.isoformat(), plant_id),
            )

    def update_interval(self, plant_id: int, interval_days: int) -> None:
        """A watering-feedback adjustment, independent of the bundled default."""
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "UPDATE plants SET interval_days=?, sync_pending=1 WHERE id=?",
                (interval_days, plant_id),
            )

    def mark_synced(self, plant_id: int, synced_watered: date) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "UPDATE plants SET synced_watered=?, sync_pending=0 WHERE id=?",
                (synced_watered.isoformat(), plant_id),
            )

    def purge_unfinished(self) -> None:
        """Drop plants whose data never finished loading (e.g. the app was closed mid-fetch)."""
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "DELETE FROM plants WHERE data_status IN (?, ?)", (LOADING, FAILED)
            )
