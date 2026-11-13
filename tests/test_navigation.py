def test_landing_page_shows_groups_as_the_active_destination(client):
    html = client.get("/").text
    assert '<a href="/" class="active">Groups</a>' in html
    assert '<a href="/upcoming" class="">Upcoming</a>' in html


def test_collection_view_shows_groups_as_the_active_destination(client, db):
    group = db.create_group("Living room")

    html = client.get(f"/groups/{group.id}").text
    assert '<a href="/" class="active">Groups</a>' in html
    assert f'<a href="/upcoming?view_group_id={group.id}" class="">Upcoming</a>' in html


def test_collection_view_all_links_upcoming_without_a_group_filter(client, db):
    db.create_group("Living room")

    html = client.get("/groups/all").text
    assert '<a href="/upcoming" class="">Upcoming</a>' in html


def test_upcoming_view_shows_upcoming_as_the_active_destination(client):
    html = client.get("/upcoming").text
    assert '<a href="/" class="">Groups</a>' in html
    assert '<a href="/upcoming" class="active">Upcoming</a>' in html
