import httpx

from app.photos import MAX_BYTES, store_photo, store_uploaded_photo


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_remote_photo_is_downloaded_and_served_from_disk(tmp_path):
    client = _client(lambda r: httpx.Response(200, content=b"\xff\xd8jpegdata", headers={"content-type": "image/jpeg"}))
    path = store_photo("https://img.example/7.jpg", tmp_path, 7, client=client)
    assert path == "/photos/7.jpg"
    assert (tmp_path / "7.jpg").read_bytes() == b"\xff\xd8jpegdata"


def test_bundled_image_is_used_as_is(tmp_path):
    assert store_photo("/static/placeholder.svg", tmp_path, 1) == "/static/placeholder.svg"
    assert list(tmp_path.iterdir()) == []


def test_failed_download_falls_back_to_no_photo(tmp_path):
    client = _client(lambda r: httpx.Response(404))
    assert store_photo("https://img.example/x.jpg", tmp_path, 1, client=client) is None


def test_non_image_response_is_rejected(tmp_path):
    client = _client(lambda r: httpx.Response(200, text="<html>", headers={"content-type": "text/html"}))
    assert store_photo("https://img.example/x", tmp_path, 1, client=client) is None
    assert store_photo(None, tmp_path, 1) is None


def test_downloaded_photo_is_still_served_when_the_network_is_gone(client, config):
    (config.photos_dir).mkdir(parents=True, exist_ok=True)
    (config.photos_dir / "3.jpg").write_bytes(b"jpegdata")
    assert client.get("/photos/3.jpg").content == b"jpegdata"


# --- user-uploaded photos --------------------------------------------------------------


def test_uploaded_photo_is_saved_and_served(tmp_path):
    path = store_uploaded_photo(b"\xff\xd8jpegdata", "image/jpeg", tmp_path, 5)
    assert path == "/photos/5.jpg"
    assert (tmp_path / "5.jpg").read_bytes() == b"\xff\xd8jpegdata"


def test_uploaded_photo_of_an_unsupported_type_is_rejected(tmp_path):
    assert store_uploaded_photo(b"not an image", "text/plain", tmp_path, 5) is None
    assert list(tmp_path.iterdir()) == []


def test_uploaded_photo_over_the_size_limit_is_rejected(tmp_path):
    oversized = b"x" * (MAX_BYTES + 1)
    assert store_uploaded_photo(oversized, "image/jpeg", tmp_path, 5) is None
    assert list(tmp_path.iterdir()) == []


def test_uploading_a_different_format_removes_the_old_file(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "5.jpg").write_bytes(b"old jpeg")
    path = store_uploaded_photo(b"new png data", "image/png", tmp_path, 5)
    assert path == "/photos/5.png"
    assert (tmp_path / "5.png").read_bytes() == b"new png data"
    assert not (tmp_path / "5.jpg").exists()


def test_a_prefix_keeps_a_plant_and_a_group_with_the_same_id_from_colliding(tmp_path):
    plant_path = store_uploaded_photo(b"plant photo", "image/jpeg", tmp_path, 5)
    group_path = store_uploaded_photo(b"group photo", "image/jpeg", tmp_path, 5, prefix="group-")
    assert plant_path == "/photos/5.jpg"
    assert group_path == "/photos/group-5.jpg"
    assert (tmp_path / "5.jpg").read_bytes() == b"plant photo"
    assert (tmp_path / "group-5.jpg").read_bytes() == b"group photo"
