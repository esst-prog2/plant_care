from datetime import date, datetime, timedelta

import pytest

from app.care import DUE, OK, OVERDUE, days_left, paginate, status_of
from tests.conftest import TODAY


def test_new_plant_has_full_interval():
    assert days_left(TODAY, 7, TODAY) == 7


def test_countdown_decreases_with_time():
    assert days_left(TODAY, 7, TODAY + timedelta(days=1)) == 6


def test_countdown_correct_after_app_was_closed_for_three_days():
    assert days_left(TODAY, 7, TODAY + timedelta(days=3)) == 4


def test_due_today_and_two_days_overdue():
    assert status_of(days_left(TODAY, 7, TODAY + timedelta(days=7))) == DUE
    late = days_left(TODAY, 7, TODAY + timedelta(days=9))
    assert late == -2 and status_of(late) == OVERDUE
    assert status_of(3) == OK


def test_watering_at_2330_counts_for_that_date_and_drops_at_midnight():
    watered = datetime(2026, 9, 10, 23, 30).date()
    assert days_left(watered, 7, date(2026, 9, 10)) == 7
    assert days_left(watered, 7, datetime(2026, 9, 11, 0, 0).date()) == 6


@pytest.mark.parametrize(
    "total, page, expected",
    [
        (0, 1, (1, 1, 0, 0)),
        (6, 1, (1, 1, 0, 6)),
        (7, 1, (1, 2, 0, 6)),
        (7, 2, (2, 2, 6, 7)),
        (7, 99, (2, 2, 6, 7)),
        (7, 0, (1, 2, 0, 6)),
        (13, 3, (3, 3, 12, 13)),
    ],
)
def test_paginate(total, page, expected):
    pg = paginate(total, page)
    assert (pg.number, pg.pages, pg.start, pg.end) == expected


def test_page_controls_at_the_ends():
    first, last = paginate(13, 1), paginate(13, 3)
    assert not first.has_prev and first.has_next
    assert last.has_prev and not last.has_next
