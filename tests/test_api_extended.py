from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from fastapi.testclient import TestClient

import app.core.config as config_module
from app.core.config import Settings
from app.main import create_app


@dataclass
class FakePlaylistService:
    def __post_init__(self):
        self.playlists = [
            {
                "id": 1,
                "title": "Imported Playlist",
                "channel": "Chan",
                "source_url": "https://www.youtube.com/playlist?list=abc",
                "entry_count": 2,
                "kind": "imported",
            }
        ]

    def add_url(self, url: str) -> dict:
        return {"type": "video", "count": 1, "title": f"added:{url}", "item_ids": [101]}

    def preview_playlist(self, url: str):
        return SimpleNamespace(source_url=url, title="preview", channel="chan", entries=[{"id": "1"}, {"id": "2"}])

    def import_playlist(self, url: str) -> dict:
        return {"type": "playlist", "count": 2, "title": f"imported:{url}", "playlist_id": 1, "item_ids": [1, 2]}

    def list_playlists(self) -> list[dict]:
        return self.playlists

    def create_custom_playlist(self, title: str) -> dict:
        created = {
            "id": 2,
            "title": title,
            "channel": "Custom",
            "source_url": "custom://2",
            "entry_count": 0,
            "kind": "custom",
        }
        self.playlists.append(created)
        return created

    def list_playlist_entries(self, playlist_id: int) -> list[dict]:
        _ = playlist_id
        return [
            {
                "id": 7,
                "playlist_id": 1,
                "source_url": "https://www.youtube.com/watch?v=1",
                "normalized_url": "https://www.youtube.com/watch?v=1",
                "title": "track",
                "channel": "ch",
                "duration_seconds": 120,
                "thumbnail_url": None,
                "position": 1,
            }
        ]

    def add_item_to_playlist(self, playlist_id: int, url: str) -> dict:
        return {"id": 8, "playlist_id": playlist_id, "title": "added", "source_url": url, "position": 2}

    def queue_playlist(self, playlist_id: int) -> dict:
        _ = playlist_id
        return {"ok": True, "count": 2, "item_ids": [20, 21]}

    def queue_playlist_entry(self, entry_id: int) -> dict:
        _ = entry_id
        return {"ok": True, "count": 1, "item_ids": [20]}


@dataclass
class FakeEngine:
    def __post_init__(self):
        self.state = SimpleNamespace(mode=SimpleNamespace(value="idle"), now_playing_id=None, now_playing_title=None)
        self.skipped = False

    def skip_current(self) -> None:
        self.skipped = True

    def subscribe(self):
        def _gen():
            yield b"chunk-1"
            yield b"chunk-2"

        return _gen()

    def playback_progress(self) -> dict:
        return {
            "duration_seconds": 180,
            "started_at": 1000.0,
            "elapsed_seconds": 15.0,
            "progress_percent": 8.3,
        }


@dataclass
class FakeSonosService:
    def __post_init__(self):
        self.last_play = None
        self.last_group = None
        self.last_ungroup = None
        self.last_volume = None

    def discover_speakers(self, timeout: int = 2):
        _ = timeout
        return [
            SimpleNamespace(
                ip="192.168.1.10",
                name="Living Room",
                uid="RINCON_10",
                coordinator_uid="RINCON_10",
                group_member_uids=["RINCON_10"],
                volume=22,
                is_coordinator=True,
            )
        ]

    def play_stream(self, speaker_ip: str, stream_url: str) -> None:
        self.last_play = (speaker_ip, stream_url)

    def group_speaker(self, coordinator_ip: str, member_ip: str) -> None:
        self.last_group = (coordinator_ip, member_ip)

    def ungroup_speaker(self, speaker_ip: str) -> None:
        self.last_ungroup = speaker_ip

    def set_volume(self, speaker_ip: str, volume: int) -> None:
        self.last_volume = (speaker_ip, volume)


@dataclass
class FakeYtDlpService:
    def search_videos(self, query: str, limit: int = 10):
        _ = limit
        return [{"id": "abc", "title": f"result:{query}", "source_url": "https://www.youtube.com/watch?v=abc"}]


def _build_test_client(tmp_path):
    settings = Settings(
        db_url=f"sqlite+pysqlite:///{tmp_path}/extended.db",
        yt_dlp_path="/bin/echo",
        ffmpeg_path="/bin/echo",
    )
    app = create_app(settings=settings, start_engine=False)
    client = TestClient(app)
    return client, app


def test_browser_root_and_static_assets(tmp_path):
    client, _app = _build_test_client(tmp_path)
    with client:
        resp = client.get("/")
        assert resp.status_code == 200
        assert 'id="app"' in resp.text
        assert "/static/dist/app.js" in resp.text


def test_queue_playlist_and_history_endpoints(tmp_path):
    client, app = _build_test_client(tmp_path)
    with client:
        app.state.playlist_service = FakePlaylistService()
        app.state.stream_engine = FakeEngine()

        add = client.post("/queue/add", json={"url": "https://www.youtube.com/watch?v=abc"})
        assert add.status_code == 200
        assert add.json()["ok"] is True

        play_now = client.post("/queue/play-now", json={"url": "https://www.youtube.com/watch?v=abc"})
        assert play_now.status_code == 200

        preview = client.post("/playlist/preview", json={"url": "https://www.youtube.com/playlist?list=pl"})
        assert preview.status_code == 200
        assert preview.json()["count"] == 2

        imported = client.post("/playlist/import", json={"url": "https://www.youtube.com/playlist?list=pl"})
        assert imported.status_code == 200
        assert imported.json()["ok"] is True

        queue_resp = client.get("/queue")
        assert queue_resp.status_code == 200
        assert isinstance(queue_resp.json(), list)

        history_resp = client.get("/history")
        assert history_resp.status_code == 200
        assert isinstance(history_resp.json(), list)


def test_playlist_library_endpoints(tmp_path):
    client, app = _build_test_client(tmp_path)
    with client:
        app.state.playlist_service = FakePlaylistService()

        listed = client.get("/playlists")
        assert listed.status_code == 200
        assert listed.json()[0]["kind"] == "imported"

        created = client.post("/playlists/custom", json={"title": "Road Trip"})
        assert created.status_code == 200
        assert created.json()["kind"] == "custom"

        single = client.get("/playlists/1")
        assert single.status_code == 200
        assert single.json()["id"] == 1

        entries = client.get("/playlists/1/entries")
        assert entries.status_code == 200
        assert entries.json()[0]["playlist_id"] == 1

        add_entry = client.post("/playlists/1/entries", json={"url": "https://www.youtube.com/watch?v=xyz"})
        assert add_entry.status_code == 200
        assert add_entry.json()["playlist_id"] == 1

        queue_playlist = client.post("/playlists/1/queue")
        assert queue_playlist.status_code == 200
        assert queue_playlist.json()["count"] == 2

        queue_entry = client.post("/playlists/entries/7/queue")
        assert queue_entry.status_code == 200
        assert queue_entry.json()["count"] == 1


def test_stream_endpoint_returns_bytes_without_hanging(tmp_path):
    client, app = _build_test_client(tmp_path)
    with client:
        app.state.stream_engine = FakeEngine()
        with client.stream("GET", "/stream/live.mp3") as resp:
            assert resp.status_code == 200
            iterator = resp.iter_bytes()
            first = next(iterator)
            assert first.startswith(b"chunk-")


def test_state_and_search_endpoints(tmp_path):
    client, app = _build_test_client(tmp_path)
    with client:
        app.state.stream_engine = FakeEngine()
        app.state.yt_dlp_service = FakeYtDlpService()

        state = client.get("/state")
        assert state.status_code == 200
        payload = state.json()
        assert "elapsed_seconds" in payload
        assert "progress_percent" in payload

        search = client.get("/search/youtube?q=lofi")
        assert search.status_code == 200
        assert search.json()["results"][0]["title"] == "result:lofi"


def test_sonos_endpoints_use_resolved_host_ip(tmp_path, monkeypatch):
    client, app = _build_test_client(tmp_path)
    monkeypatch.setattr(config_module, "_detect_local_ip", lambda: "192.168.1.77")
    with client:
        fake_sonos = FakeSonosService()
        app.state.sonos_service = fake_sonos

        speakers = client.get("/sonos/speakers")
        assert speakers.status_code == 200
        payload = speakers.json()
        assert len(payload) == 1
        assert payload[0]["name"] == "Living Room"
        assert payload[0]["volume"] == 22

        play = client.post("/sonos/play", json={"speaker_ip": "192.168.1.10"})
        assert play.status_code == 200
        assert play.json()["ok"] is True
        assert fake_sonos.last_play[0] == "192.168.1.10"
        assert fake_sonos.last_play[1] == "http://192.168.1.77:8000/stream/live.mp3"

        group = client.post("/sonos/group", json={"coordinator_ip": "192.168.1.10", "member_ip": "192.168.1.20"})
        assert group.status_code == 200
        assert fake_sonos.last_group == ("192.168.1.10", "192.168.1.20")

        ungroup = client.post("/sonos/ungroup", json={"speaker_ip": "192.168.1.20"})
        assert ungroup.status_code == 200
        assert fake_sonos.last_ungroup == "192.168.1.20"

        volume = client.post("/sonos/volume", json={"speaker_ip": "192.168.1.20", "volume": 55})
        assert volume.status_code == 200
        assert fake_sonos.last_volume == ("192.168.1.20", 55)


def test_state_uses_host_ip_env_when_detected_ip_is_docker(tmp_path, monkeypatch):
    monkeypatch.setattr(config_module, "_detect_local_ip", lambda: "172.17.0.2")
    monkeypatch.setenv("HOST_IP", "192.168.1.88")
    client, _app = _build_test_client(tmp_path)

    with client:
        response = client.get("/state")

    assert response.status_code == 200
    assert response.json()["stream_url"] == "http://192.168.1.88:8000/stream/live.mp3"
