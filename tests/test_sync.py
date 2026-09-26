import logging
from datetime import date, datetime, timedelta, timezone

import pytest

from app.care import days_left
from app.sync import Syncer, reconcile
from app.tasks_client import RemoteTask, TasksError
from tests.conftest import TODAY, add_ready

UTC = timezone.utc
D = date  # short alias for readable dates below


def utc(month, day, hour=10, minute=0):
    return datetime(2026, month, day, hour, minute, tzinfo=UTC)


@pytest.fixture
def pilea(db, tasks):
    """A 7-day plant watered on Sep 10 whose two reminders (Sep 17, Sep 24) already exist."""
    plant = add_ready(db, "Pilea", 7, D(2026, 9, 10))
    reconcile(db, tasks, D(2026, 9, 10))
    return plant


def test_new_plant_gets_two_all_day_reminders(db, tasks):
    plant = add_ready(db, "Pilea", 7, TODAY)
    report = reconcile(db, tasks, TODAY)
    assert report.created == 2
    assert tasks.dues_for(plant.id) == [D(2026, 9, 17), D(2026, 9, 24)]
    assert {t.title for t in tasks.tasks.values()} == {"Water Pilea"}
    assert all(t.plant_id == plant.id for t in tasks.tasks.values())


def test_syncing_again_changes_nothing_and_keeps_two_open(db, tasks, pilea):
    tasks.calls.clear()
    reconcile(db, tasks, D(2026, 9, 11))
    assert tasks.calls == []
    assert len(tasks.open_for(pilea.id)) == 2


def test_sync_pending_is_cleared_after_a_successful_sync(db, tasks):
    plant = add_ready(db, "Pilea", 7, TODAY)
    assert db.get_plant(plant.id).sync_pending is True
    reconcile(db, tasks, TODAY)
    after = db.get_plant(plant.id)
    assert after.sync_pending is False and after.synced_watered == TODAY


def test_failed_sync_leaves_the_change_pending_and_a_later_sync_catches_up(db, tasks):
    plant = add_ready(db, "Pilea", 7, TODAY)
    tasks.fail = True
    with pytest.raises(TasksError):
        reconcile(db, tasks, TODAY)
    assert db.get_plant(plant.id).sync_pending is True
    tasks.fail = False
    reconcile(db, tasks, TODAY)
    assert db.get_plant(plant.id).sync_pending is False
    assert len(tasks.open_for(plant.id)) == 2


# --- a tick on the phone ---------------------------------------------------------------


def test_tick_while_computer_was_off_counts_from_the_tick(db, tasks, pilea):
    first = tasks.open_for(pilea.id)[0]
    tasks.tick(first.id, utc(9, 12))
    today = D(2026, 9, 15)  # the computer is switched on three days later
    reconcile(db, tasks, today)
    plant = db.get_plant(pilea.id)
    assert plant.last_watered == D(2026, 9, 12)
    assert days_left(plant.last_watered, plant.interval_days, today) == 4
    assert tasks.dues_for(pilea.id) == [D(2026, 9, 19), D(2026, 9, 26)]


def test_computer_off_after_a_tick_leaves_the_second_reminder_waiting(db, tasks, pilea):
    tasks.tick(tasks.open_for(pilea.id)[0].id, utc(9, 12))
    open_now = tasks.open_for(pilea.id)
    assert [t.due for t in open_now] == [D(2026, 9, 24)]  # still there without any sync


def test_tick_before_the_due_date(db, tasks, pilea):
    tasks.tick(tasks.open_for(pilea.id)[0].id, utc(9, 15))  # due Sep 17
    reconcile(db, tasks, D(2026, 9, 15))
    assert db.get_plant(pilea.id).last_watered == D(2026, 9, 15)
    assert tasks.dues_for(pilea.id) == [D(2026, 9, 22), D(2026, 9, 29)]


def test_tick_after_the_due_date_uses_the_tick_date(db, tasks, pilea):
    tasks.tick(tasks.open_for(pilea.id)[0].id, utc(9, 19))  # two days after Sep 17
    reconcile(db, tasks, D(2026, 9, 19))
    assert db.get_plant(pilea.id).last_watered == D(2026, 9, 19)


def test_late_evening_tick_counts_for_the_local_date(db, tasks, pilea):
    late = datetime(2026, 9, 13, 4, 30, tzinfo=UTC)  # 23:30 on Sep 12 at UTC-5
    tasks.tick(tasks.open_for(pilea.id)[0].id, late)
    reconcile(db, tasks, D(2026, 9, 15), tz=timezone(timedelta(hours=-5)))
    assert db.get_plant(pilea.id).last_watered == D(2026, 9, 12)


def test_ticking_the_second_reminder_counts_too(db, tasks, pilea):
    second = tasks.open_for(pilea.id)[1]  # due Sep 24
    tasks.tick(second.id, utc(9, 20))
    reconcile(db, tasks, D(2026, 9, 20))
    assert db.get_plant(pilea.id).last_watered == D(2026, 9, 20)
    assert tasks.dues_for(pilea.id) == [D(2026, 9, 27), D(2026, 10, 4)]


def test_a_tick_in_the_future_is_capped_at_today(db, tasks, pilea):
    tasks.tick(tasks.open_for(pilea.id)[0].id, utc(9, 30))
    reconcile(db, tasks, D(2026, 9, 12))
    assert db.get_plant(pilea.id).last_watered == D(2026, 9, 12)


def test_the_latest_of_several_ticks_wins(db, tasks, pilea):
    first, second = tasks.open_for(pilea.id)
    tasks.tick(first.id, utc(9, 12))
    tasks.tick(second.id, utc(9, 14))
    reconcile(db, tasks, D(2026, 9, 16))
    assert db.get_plant(pilea.id).last_watered == D(2026, 9, 14)


def test_a_tick_is_only_counted_once(db, tasks, pilea):
    tasks.tick(tasks.open_for(pilea.id)[0].id, utc(9, 12))
    reconcile(db, tasks, D(2026, 9, 15))
    tasks.calls.clear()
    reconcile(db, tasks, D(2026, 9, 16))
    assert tasks.calls == [] and db.get_plant(pilea.id).last_watered == D(2026, 9, 12)


# --- watering in the app ---------------------------------------------------------------


def test_watering_in_the_app_completes_the_earliest_reminder_and_realigns(db, tasks, pilea):
    first_id = tasks.open_for(pilea.id)[0].id
    db.mark_watered(pilea.id, D(2026, 9, 17))
    reconcile(db, tasks, D(2026, 9, 17))
    assert tasks.tasks[first_id].is_completed and tasks.tasks[first_id].recorded
    assert tasks.dues_for(pilea.id) == [D(2026, 9, 24), D(2026, 10, 1)]


def test_a_reminder_completed_by_the_app_is_not_read_back_as_a_tick(db, tasks, pilea):
    db.mark_watered(pilea.id, D(2026, 9, 17))
    reconcile(db, tasks, D(2026, 9, 17))
    tasks.calls.clear()
    reconcile(db, tasks, D(2026, 9, 25))  # much later: the completion time of that task is "now"
    assert tasks.calls == []
    assert db.get_plant(pilea.id).last_watered == D(2026, 9, 17)


def test_when_both_places_record_a_watering_the_later_date_wins(db, tasks, pilea):
    tasks.tick(tasks.open_for(pilea.id)[0].id, utc(9, 16))  # phone, yesterday
    db.mark_watered(pilea.id, D(2026, 9, 17))  # app, today, before any sync
    reconcile(db, tasks, D(2026, 9, 17))
    assert db.get_plant(pilea.id).last_watered == D(2026, 9, 17)
    assert tasks.dues_for(pilea.id) == [D(2026, 9, 24), D(2026, 10, 1)]


# --- keeping the reminders correct -----------------------------------------------------


def test_a_reminder_deleted_in_google_is_created_again(db, tasks, pilea):
    tasks.user_deletes(tasks.open_for(pilea.id)[0].id)
    reconcile(db, tasks, D(2026, 9, 11))
    assert tasks.dues_for(pilea.id) == [D(2026, 9, 17), D(2026, 9, 24)]


def test_a_moved_due_date_is_restored(db, tasks, pilea):
    tasks.user_moves(tasks.open_for(pilea.id)[0].id, D(2026, 9, 30))
    reconcile(db, tasks, D(2026, 9, 11))
    assert tasks.dues_for(pilea.id) == [D(2026, 9, 17), D(2026, 9, 24)]


def test_a_changed_interval_moves_both_reminders(db, tasks, pilea):
    db.complete_plant(pilea.id, "/static/placeholder.svg", "Bright light", 14, "local")
    reconcile(db, tasks, D(2026, 9, 11))
    assert tasks.dues_for(pilea.id) == [D(2026, 9, 24), D(2026, 10, 8)]


def test_a_third_open_reminder_is_deleted(db, tasks, pilea):
    tasks.create_task(pilea.id, "Water Pilea", D(2026, 10, 15))
    reconcile(db, tasks, D(2026, 9, 11))
    assert tasks.dues_for(pilea.id) == [D(2026, 9, 17), D(2026, 9, 24)]


def test_removing_a_plant_deletes_its_reminders_on_the_next_sync(db, tasks, pilea):
    db.delete_plant(pilea.id)
    reconcile(db, tasks, D(2026, 9, 11))
    assert tasks.tasks == {}


def test_removal_while_google_is_down_is_finished_later(db, tasks, pilea):
    db.delete_plant(pilea.id)
    tasks.fail = True
    with pytest.raises(TasksError):
        reconcile(db, tasks, D(2026, 9, 11))
    tasks.fail = False
    reconcile(db, tasks, D(2026, 9, 11))
    assert tasks.tasks == {}


def test_a_stray_reminder_in_the_list_is_deleted(db, tasks, pilea):
    stray = tasks.user_adds_stray("No plant owns this", plant_id=None)
    ghost = tasks.user_adds_stray("Plant 999", plant_id=999)
    reconcile(db, tasks, D(2026, 9, 11))
    assert stray.id not in tasks.tasks and ghost.id not in tasks.tasks
    assert len(tasks.open_for(pilea.id)) == 2


def test_a_plant_that_is_still_loading_keeps_its_reminders_untouched(db, tasks):
    loading = db.add_plant("local:pilea", "Pilea", TODAY)
    tasks.create_task(loading.id, "Water Pilea", D(2026, 9, 17))
    reconcile(db, tasks, TODAY)
    assert len(tasks.tasks) == 1


def test_the_sync_only_touches_tasks_it_was_shown(db, tasks, pilea):
    tasks.calls.clear()
    reconcile(db, tasks, D(2026, 9, 12))
    touched = {call[1] for call in tasks.calls if call[0] in ("update", "delete", "complete")}
    assert touched <= set(tasks.tasks)


# --- the runner ------------------------------------------------------------------------


def test_syncer_logs_a_failure_and_never_raises(db, tasks, caplog):
    add_ready(db, "Pilea", 7, TODAY)
    tasks.fail = True
    syncer = Syncer(db, tasks, lambda: TODAY)
    with caplog.at_level(logging.ERROR, logger="plant_care"):
        assert syncer.run() is None
    assert "Google sync failed" in caplog.text


def test_syncer_returns_the_report_on_success(db, tasks):
    add_ready(db, "Pilea", 7, TODAY)
    report = Syncer(db, tasks, lambda: TODAY).run()
    assert report is not None and report.created == 2


def test_overlapping_runs_are_coalesced(db, tasks):
    add_ready(db, "Pilea", 7, TODAY)
    syncer = Syncer(db, tasks, lambda: TODAY)
    syncer._lock.acquire()
    try:
        assert syncer.run() is None  # busy: it asks the running sync to go round again
        assert syncer._again is True
    finally:
        syncer._lock.release()
    assert RemoteTask  # the interface type stays importable for the fake


# --- the standalone command ------------------------------------------------------------


def test_sync_command_runs_one_sync_and_reports(config, db, tasks, monkeypatch, capsys):
    import sync_tasks

    add_ready(db, "Pilea", 7, date.today())
    monkeypatch.setattr(sync_tasks, "load_config", lambda: config)
    monkeypatch.setattr(sync_tasks, "build_tasks_client", lambda cfg: tasks)
    assert sync_tasks.main() == 0
    assert "2 to-do(s) created" in capsys.readouterr().out
    assert len(tasks.tasks) == 2


def test_sync_command_says_so_when_google_is_not_configured(config, monkeypatch, capsys):
    import sync_tasks

    monkeypatch.setattr(sync_tasks, "load_config", lambda: config)
    assert sync_tasks.main() == 2
    assert "not configured" in capsys.readouterr().out


def test_sync_command_reports_a_failure(config, db, tasks, monkeypatch, capsys):
    import sync_tasks

    add_ready(db, "Pilea", 7, date.today())
    tasks.fail = True
    monkeypatch.setattr(sync_tasks, "load_config", lambda: config)
    monkeypatch.setattr(sync_tasks, "build_tasks_client", lambda cfg: tasks)
    assert sync_tasks.main() == 1
    assert "Sync failed" in capsys.readouterr().out
