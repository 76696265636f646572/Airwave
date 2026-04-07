from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.common.serializers import _serialize_state
from app.core.config import Settings
from app.db.repository import NewQueueItem
from app.main import create_app


def test_health_and_state_endpoints(tmp_path):
    settings = Settings(
        db_url=f"sqlite+pysqlite:///{tmp_path}/api.db",
        yt_dlp_path="/bin/echo",
        ffmpeg_path="/bin/echo",
    )
    app = create_app(settings=settings, start_engine=False)
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        state = client.get("/api/state")
        assert state.status_code == 200
        payload = state.json()
        assert payload["mode"] in ("idle", "playing")
        assert payload["paused"] in (True, False)
        assert payload["repeat_mode"] in ("off", "all", "one")
        assert payload["shuffle_enabled"] in (True, False)
        assert payload["now_playing_is_liked"] in (True, False)
        assert payload["stream_url"].endswith("/stream/live.mp3")


def test_serialize_state_prefers_hq_youtube_thumbnail_over_maxres():
    engine = SimpleNamespace(
        state=SimpleNamespace(
            mode=SimpleNamespace(value="playing"),
            paused=False,
            repeat_mode=SimpleNamespace(value="off"),
            shuffle_enabled=False,
            now_playing_id=1,
            now_playing_title="t",
            now_playing_channel=None,
            now_playing_thumbnail_url="https://i.ytimg.com/vi/abc123/maxresdefault.jpg",
            now_playing_is_live=False,
            now_playing_duration_seconds=60,
        ),
        playback_progress=lambda: {
            "duration_seconds": 60,
            "started_at": None,
            "elapsed_seconds": None,
            "progress_percent": None,
        },
    )
    out = _serialize_state(engine, "http://example.com/stream/live.mp3")
    assert out["now_playing_thumbnail_url"] == "https://i.ytimg.com/vi/abc123/hqdefault.jpg"
    assert out["now_playing_is_liked"] is False


def test_like_current_song_endpoint_adds_to_liked_songs(tmp_path):
    settings = Settings(
        db_url=f"sqlite+pysqlite:///{tmp_path}/api_like.db",
        yt_dlp_path="/bin/echo",
        ffmpeg_path="/bin/echo",
    )
    app = create_app(settings=settings, start_engine=False)

    with TestClient(app) as client:
        repo = client.app.state.repository
        engine = client.app.state.stream_engine
        created = repo.enqueue_items(
            [NewQueueItem(source_url="u1", normalized_url="u1", source_type="video", title="T")]
        )[0]
        engine.state.now_playing_id = created.id
        engine.state.now_playing_title = created.title

        liked = client.post("/api/state/like")
        assert liked.status_code == 200
        body = liked.json()
        assert body["ok"] is True
        assert body["liked"] is True
        assert body["state"]["now_playing_is_liked"] is True

        playlists = client.get("/api/playlists").json()
        liked_pl = next(p for p in playlists if p["source_url"] == "custom://liked_songs")
        entries = client.get(f"/api/playlists/{liked_pl['id']}/entries").json()
        assert any(e["source_url"] == "u1" for e in entries)


def test_unlike_current_song_endpoint_removes_from_liked_songs(tmp_path):
    settings = Settings(
        db_url=f"sqlite+pysqlite:///{tmp_path}/api_unlike.db",
        yt_dlp_path="/bin/echo",
        ffmpeg_path="/bin/echo",
    )
    app = create_app(settings=settings, start_engine=False)

    with TestClient(app) as client:
        repo = client.app.state.repository
        engine = client.app.state.stream_engine
        created = repo.enqueue_items(
            [NewQueueItem(source_url="u1", normalized_url="u1", source_type="video", title="T")]
        )[0]
        engine.state.now_playing_id = created.id
        engine.state.now_playing_title = created.title

        liked = client.post("/api/state/like")
        assert liked.status_code == 200
        assert liked.json()["state"]["now_playing_is_liked"] is True

        unliked = client.post("/api/state/unlike")
        assert unliked.status_code == 200
        body = unliked.json()
        assert body["ok"] is True
        assert body["unliked"] is True
        assert body["removed"] >= 1
        assert body["state"]["now_playing_is_liked"] is False

        playlists = client.get("/api/playlists").json()
        liked_pl = next(p for p in playlists if p["source_url"] == "custom://liked_songs")
        entries = client.get(f"/api/playlists/{liked_pl['id']}/entries").json()
        assert not any(e["source_url"] == "u1" for e in entries)
