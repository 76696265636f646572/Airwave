from __future__ import annotations

import json
import subprocess
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.services.resolver.base import PlaylistPreview, ResolvedTrack, ResolverError, SourceResolver
from app.services.resolver.utils import is_youtube_url, source_site_from_url


class YtDlpError(ResolverError):
    pass


SEARCH_PREFIXES = {
    "youtube": "ytsearch",
    "soundcloud": "scsearch",
    "vimeo": "vimsearch",
}


class YtDlpResolver(SourceResolver):
    def __init__(
        self,
        binary_path: str,
        *,
        blocked_domains: list[str] | None = None,
        blocked_extractors: list[str] | None = None,
    ) -> None:
        self.binary_path = binary_path
        self.blocked_domains = [d.lower().strip() for d in (blocked_domains or []) if d.strip()]
        self.blocked_extractors = [e.lower().strip() for e in (blocked_extractors or []) if e.strip()]

    def normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.netloc.endswith("youtu.be"):
            video_id = parsed.path.lstrip("/")
            return f"https://www.youtube.com/watch?v={video_id}"
        if "youtube.com" in parsed.netloc:
            query = parse_qs(parsed.query)
            video_id = query.get("v", [None])[0]
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"
            playlist_id = query.get("list", [None])[0]
            if playlist_id:
                return f"https://www.youtube.com/playlist?list={playlist_id}"
        return url

    def _run_json(self, *args: str) -> dict[str, Any]:
        cmd = [self.binary_path, *args]
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise YtDlpError(completed.stderr.strip() or "yt-dlp failed")
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise YtDlpError("Invalid JSON from yt-dlp") from exc

    def _ensure_domain_allowed(self, url: str) -> None:
        host = (urlparse(url).hostname or "").lower()
        if not host:
            return
        for blocked in self.blocked_domains:
            if host == blocked or host.endswith(f".{blocked}"):
                raise YtDlpError("This site is not allowed")

    def _extract_entry_url(self, entry: dict[str, Any]) -> str | None:
        webpage_url = entry.get("webpage_url")
        if isinstance(webpage_url, str) and webpage_url.startswith("http"):
            return webpage_url
        raw_url = entry.get("url")
        if isinstance(raw_url, str) and raw_url.startswith("http"):
            return raw_url
        video_id = entry.get("id")
        extractor = (entry.get("extractor") or entry.get("extractor_key") or "").lower()
        if video_id and ("youtube" in extractor):
            return f"https://www.youtube.com/watch?v={video_id}"
        return None

    def is_playlist_url(self, url: str) -> bool:
        normalized = self.normalize_url(url)
        self._ensure_domain_allowed(normalized)
        parsed = urlparse(normalized)
        query = parse_qs(parsed.query)
        if is_youtube_url(normalized):
            if "watch" in parsed.path:
                return False
            if "/playlist" in parsed.path and "list" in query:
                return True
        data = self._run_json("--flat-playlist", "--skip-download", "-J", normalized)
        entries = data.get("entries")
        if not isinstance(entries, list) or not entries:
            return False
        if data.get("_type") == "playlist":
            return True
        return len(entries) > 1

    def spawn_audio_stream(self, url: str) -> subprocess.Popen[bytes]:
        normalized = self.normalize_url(url)
        self._ensure_domain_allowed(normalized)
        cmd = [
            self.binary_path,
            "--no-playlist",
            "-f",
            "bestaudio/best",
            "--no-progress",
            "--quiet",
            "-o",
            "-",
            normalized,
        ]
        try:
            return subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise YtDlpError(
                f"yt-dlp binary not found at '{self.binary_path}'. "
                "Install yt-dlp or set MYTUBE_YT_DLP_PATH."
            ) from exc

    def resolve_video(self, url: str) -> ResolvedTrack:
        normalized = self.normalize_url(url)
        self._ensure_domain_allowed(normalized)
        data = self._run_json("--no-playlist", "-f", "bestaudio/best", "--skip-download", "-J", normalized)
        direct_url = data.get("url")
        if not direct_url:
            raise YtDlpError("Could not resolve direct stream URL")
        is_live = bool(data.get("is_live")) or str(data.get("live_status") or "").lower() in {"is_live", "post_live"}
        duration = data.get("duration")
        if not isinstance(duration, int):
            duration = None
        return ResolvedTrack(
            source_url=url,
            normalized_url=normalized,
            title=data.get("title"),
            channel=data.get("uploader") or data.get("channel"),
            duration_seconds=duration,
            thumbnail_url=data.get("thumbnail"),
            stream_url=direct_url,
            source_site=source_site_from_url(normalized),
            is_live=is_live,
            can_seek=bool((duration or 0) > 0 and not is_live),
        )

    def preview_playlist(self, url: str) -> PlaylistPreview:
        normalized = self.normalize_url(url)
        self._ensure_domain_allowed(normalized)
        data = self._run_json("--flat-playlist", "--skip-download", "-J", normalized)
        entries: list[dict[str, Any]] = []
        for entry in data.get("entries", []):
            if not isinstance(entry, dict):
                continue
            source_url = self._extract_entry_url(entry)
            if not source_url:
                continue
            duration = entry.get("duration")
            if not isinstance(duration, int):
                duration = None
            entries.append(
                {
                    "source_url": source_url,
                    "normalized_url": source_url,
                    "title": entry.get("title"),
                    "channel": entry.get("uploader") or entry.get("channel"),
                    "duration_seconds": duration,
                    "thumbnail_url": entry.get("thumbnail"),
                    "source_site": source_site_from_url(source_url),
                    "is_live": bool(entry.get("is_live")),
                }
            )
        return PlaylistPreview(
            source_url=normalized,
            title=data.get("title"),
            channel=data.get("uploader") or data.get("channel"),
            entries=entries,
            thumbnail_url=data.get("thumbnail"),
        )

    def search(self, query: str, site: str = "youtube", limit: int = 10) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 25))
        site_key = (site or "youtube").strip().lower()
        prefix = SEARCH_PREFIXES.get(site_key, SEARCH_PREFIXES["youtube"])
        payload = self._run_json("--flat-playlist", "--skip-download", "-J", f"{prefix}{bounded_limit}:{query}")
        results: list[dict[str, Any]] = []
        for entry in payload.get("entries", []):
            if not isinstance(entry, dict):
                continue
            source_url = self._extract_entry_url(entry)
            if not source_url:
                continue
            duration = entry.get("duration")
            if not isinstance(duration, int):
                duration = None
            results.append(
                {
                    "id": entry.get("id") or source_url,
                    "source_url": source_url,
                    "normalized_url": source_url,
                    "title": entry.get("title"),
                    "channel": entry.get("uploader") or entry.get("channel"),
                    "duration_seconds": duration,
                    "thumbnail_url": entry.get("thumbnail"),
                    "source_site": source_site_from_url(source_url) or site_key.capitalize(),
                    "site": site_key,
                }
            )
        return results

