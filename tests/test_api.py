from fastapi.testclient import TestClient

from app.core.config import Settings
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
        assert payload["stream_url"].endswith("/stream/live.mp3")


def test_cookie_settings_endpoints(tmp_path):
    settings = Settings(
        db_url=f"sqlite+pysqlite:///{tmp_path}/cookies.db",
        yt_dlp_path="/bin/echo",
        ffmpeg_path="/bin/echo",
    )
    app = create_app(settings=settings, start_engine=False)
    with TestClient(app) as client:
        # GET returns provider status (never values)
        r = client.get("/api/settings/cookies")
        assert r.status_code == 200
        data = r.json()
        assert "providers" in data
        assert data["providers"]["youtube"] is False

        # PUT sets cookie
        r = client.put(
            "/api/settings/cookies",
            json={"provider": "youtube", "value": "# Netscape HTTP Cookie File\ndomain\tpath\tname\tvalue"},
        )
        assert r.status_code == 200
        assert r.json()["ok"] is True

        # GET now shows configured
        r = client.get("/api/settings/cookies")
        assert r.status_code == 200
        assert r.json()["providers"]["youtube"] is True

        # DELETE removes cookie
        r = client.delete("/api/settings/cookies/youtube")
        assert r.status_code == 200
        r = client.get("/api/settings/cookies")
        assert r.json()["providers"]["youtube"] is False

        # Unknown provider rejected
        r = client.put("/api/settings/cookies", json={"provider": "unknown", "value": "x"})
        assert r.status_code == 400
