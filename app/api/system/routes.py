from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.api.common.dependencies import _services
from app.api.common.serializers import _publish_ui_snapshot, _serialize_state, _stream_url
from app.db.repository import NewPlaylistEntry
from app.services.stream_engine import StreamEngine

router = APIRouter()


@router.get("/health")
def health(request: Request) -> dict[str, str]:
    services = _services(request)
    return {"status": "ok", "mode": services["engine"].state.mode.value}


@router.get("/state")
def state(request: Request) -> dict[str, Any]:
    services = _services(request)
    engine: StreamEngine = services["engine"]
    return _serialize_state(engine, _stream_url(request), repo=services["repo"])


@router.post("/state/like")
def like_current_song(request: Request) -> dict[str, Any]:
    services = _services(request)
    engine: StreamEngine = services["engine"]
    now_playing_id = engine.state.now_playing_id
    if now_playing_id is None:
        raise HTTPException(status_code=409, detail="No active track")

    repo = services["repo"]
    playlist_service = services["playlist"]
    liked_playlist = repo.get_playlist_by_source_url("custom://liked_songs")
    if liked_playlist is None:
        raise HTTPException(status_code=500, detail="Liked Songs playlist is missing")

    item = repo.get_item(now_playing_id)
    if item is None:
        raise HTTPException(status_code=409, detail="Active track is missing")

    entry = {
        "source_url": item.source_url,
        "provider": getattr(item, "provider", None),
        "provider_item_id": getattr(item, "provider_item_id", None),
        "normalized_url": getattr(item, "normalized_url", None) or item.source_url,
        "title": getattr(item, "title", None),
        "channel": getattr(item, "channel", None),
        "duration_seconds": getattr(item, "duration_seconds", None),
        "thumbnail_url": getattr(item, "thumbnail_url", None),
    }

    created = playlist_service.add_entries_to_playlist(
        liked_playlist.id,
        entries=[NewPlaylistEntry(**entry)],
        import_mode="skip_duplicates",
    )
    _publish_ui_snapshot(request)
    return {
        "ok": True,
        "liked": True,
        "skipped_duplicates": bool(created.get("skipped_duplicates")),
        "state": _serialize_state(engine, _stream_url(request), repo=repo),
    }


@router.post("/state/unlike")
def unlike_current_song(request: Request) -> dict[str, Any]:
    services = _services(request)
    engine: StreamEngine = services["engine"]
    now_playing_id = engine.state.now_playing_id
    if now_playing_id is None:
        raise HTTPException(status_code=409, detail="No active track")

    repo = services["repo"]
    liked_playlist = repo.get_playlist_by_source_url("custom://liked_songs")
    if liked_playlist is None:
        raise HTTPException(status_code=500, detail="Liked Songs playlist is missing")

    item = repo.get_item(now_playing_id)
    if item is None:
        raise HTTPException(status_code=409, detail="Active track is missing")

    removed = repo.remove_playlist_track(
        liked_playlist.id,
        normalized_url=getattr(item, "normalized_url", None) or item.source_url,
        provider_item_id=getattr(item, "provider_item_id", None),
    )
    _publish_ui_snapshot(request)
    return {
        "ok": True,
        "unliked": True,
        "removed": removed,
        "state": _serialize_state(engine, _stream_url(request), repo=repo),
    }
