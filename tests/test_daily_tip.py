from datetime import timedelta

from tests.conftest import TODAY, Clock


def test_daily_tip_is_the_same_message_every_time_on_the_same_date(make_client):
    html_1 = make_client(clock_override=Clock(TODAY)).get("/").text
    html_2 = make_client(clock_override=Clock(TODAY)).get("/").text

    message = html_1.split('class="daily-tip">', 1)[1].split("</p>", 1)[0]
    assert message in html_2


def test_daily_tip_repeats_after_ten_days(make_client):
    html_today = make_client(clock_override=Clock(TODAY)).get("/").text
    html_ten_days_later = make_client(clock_override=Clock(TODAY + timedelta(days=10))).get("/").text

    message_today = html_today.split('class="daily-tip">', 1)[1].split("</p>", 1)[0]
    message_later = html_ten_days_later.split('class="daily-tip">', 1)[1].split("</p>", 1)[0]
    assert message_today == message_later


def test_daily_tip_changes_on_a_different_day(make_client):
    html_today = make_client(clock_override=Clock(TODAY)).get("/").text
    html_tomorrow = make_client(clock_override=Clock(TODAY + timedelta(days=1))).get("/").text

    message_today = html_today.split('class="daily-tip">', 1)[1].split("</p>", 1)[0]
    message_tomorrow = html_tomorrow.split('class="daily-tip">', 1)[1].split("</p>", 1)[0]
    assert message_today != message_tomorrow


def test_daily_tip_appears_identically_on_every_page(make_client, db):
    group = db.create_group("Living room")
    client = make_client(clock_override=Clock(TODAY))

    landing_html = client.get("/").text
    collection_html = client.get(f"/groups/{group.id}").text
    upcoming_html = client.get("/upcoming").text

    message = landing_html.split('class="daily-tip">', 1)[1].split("</p>", 1)[0]
    assert message in collection_html
    assert message in upcoming_html
