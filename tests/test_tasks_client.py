import json
from datetime import date, datetime, timezone

import httpx
import pytest

from app.tasks_client import AppsScriptClient, TasksError, make_notes, parse_notes

URL = "https://script.google.com/macros/s/EXAMPLE/exec"


def _client(handler):
    http = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)
    return AppsScriptClient(URL, "s3cret", client=http)


def _ok(payload):
    return httpx.Response(200, json={"ok": True, **payload})


def test_notes_marker_round_trip():
    assert parse_notes(make_notes(12)) == (12, False)
    assert parse_notes(make_notes(12, recorded=True)) == (12, True)
    assert parse_notes("Buy soil") == (None, False)
    assert parse_notes(None) == (None, False)


def test_list_parses_tasks_dates_and_completion():
    def handler(request):
        body = json.loads(request.content)
        assert body == {"secret": "s3cret", "action": "list"}
        return _ok(
            {
                "tasks": [
                    {"id": "a", "title": "Water Pilea", "notes": "plant_care:3",
                     "due": "2026-09-17T00:00:00.000Z", "status": "needsAction", "completed": None},
                    {"id": "b", "title": "Water Pilea", "notes": "plant_care:3 recorded",
                     "due": "2026-09-10T00:00:00.000Z", "status": "completed",
                     "completed": "2026-09-12T22:31:00.000Z"},
                    {"id": "c", "title": "Loose", "notes": "", "due": None, "status": "needsAction"},
                ]
            }
        )

    open_task, done, loose = _client(handler).list_tasks()
    assert (open_task.plant_id, open_task.due, open_task.is_completed) == (3, date(2026, 9, 17), False)
    assert done.completed == datetime(2026, 9, 12, 22, 31, tzinfo=timezone.utc) and done.recorded
    assert loose.plant_id is None and loose.due is None


def test_create_update_complete_delete_send_the_right_requests():
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        return _ok({"task": {"id": "n1", "title": "Water Pilea", "notes": "plant_care:3",
                             "due": "2026-09-17T00:00:00.000Z", "status": "needsAction"}})

    client = _client(handler)
    created = client.create_task(3, "Water Pilea", date(2026, 9, 17))
    client.update_task("n1", "Water Pilea", date(2026, 9, 24))
    client.complete_task("n1")
    client.delete_task("n1")
    assert created.id == "n1" and created.plant_id == 3
    assert seen[0] == {"secret": "s3cret", "action": "create", "title": "Water Pilea",
                       "due": "2026-09-17", "notes": "plant_care:3"}
    assert seen[1]["action"] == "update" and seen[1]["due"] == "2026-09-24"
    assert seen[2]["action"] == "complete" and seen[2]["recordedWord"] == "recorded"
    assert seen[3] == {"secret": "s3cret", "action": "delete", "id": "n1"}


def test_apps_script_answers_through_a_redirect():
    def handler(request):
        if request.method == "POST":
            return httpx.Response(302, headers={"location": "https://script.googleusercontent.com/echo?x=1"})
        return _ok({"tasks": []})

    assert _client(handler).list_tasks() == []


def _failures():
    def network(request):
        raise httpx.ConnectError("no internet", request=request)

    return {
        "network": network,
        "timeout": lambda r: (_ for _ in ()).throw(httpx.ReadTimeout("slow", request=r)),
        "server error": lambda r: httpx.Response(500, text="oops"),
        "not json": lambda r: httpx.Response(200, text="<html>sign in</html>"),
        "refused": lambda r: httpx.Response(200, json={"ok": False, "error": "bad secret"}),
    }


@pytest.mark.parametrize("name", list(_failures()))
def test_every_failure_becomes_a_tasks_error(name):
    with pytest.raises(TasksError):
        _client(_failures()[name]).list_tasks()


def test_errors_never_contain_the_private_web_app_address():
    def handler(request):
        return httpx.Response(404, request=request)

    with pytest.raises(TasksError) as caught:
        _client(handler).list_tasks()
    assert URL not in str(caught.value) and "s3cret" not in str(caught.value)
    assert caught.value.__cause__ is None and caught.value.__suppress_context__


def test_request_logging_of_urls_is_switched_off():
    import logging

    import app.tasks_client  # noqa: F401  (importing it configures the logger)

    assert logging.getLogger("httpx").level >= logging.WARNING
