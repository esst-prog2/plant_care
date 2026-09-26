"""Run one Google Tasks sync by hand: python sync_tasks.py"""

from __future__ import annotations

import sys
from datetime import date

from app.config import build_tasks_client, load_config
from app.db import Database
from app.sync import reconcile
from app.tasks_client import TasksError


def main() -> int:
    config = load_config()
    client = build_tasks_client(config)
    if client is None:
        print("Google reminders are not configured (set GOOGLE_SCRIPT_URL and GOOGLE_SCRIPT_SECRET).")
        return 2
    db = Database(config.db_path)
    db.init()
    try:
        report = reconcile(db, client, date.today())
    except TasksError as exc:
        print(f"Sync failed: {exc}")
        return 1
    print(f"Sync done: {report.summary()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
