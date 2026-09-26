import httpx

from app.photos import store_photo


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
