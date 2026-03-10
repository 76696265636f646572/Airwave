from __future__ import annotations

import os
import subprocess
from urllib.parse import urlparse

from app.services.resolver.base import PlaylistPreview, ResolvedTrack, ResolverError, SourceResolver
from app.services.resolver.utils import source_site_from_url


class DirectUrlError(ResolverError):
    pass


KNOWN_NON_DIRECT_DOMAINS = (
    "youtube.com",
    "youtu.be",
    "soundcloud.com",
    "vimeo.com",
    "twitch.tv",
)

LIVE_MARKERS = ("live", "stream", "radio", ".m3u8", "icy", "icecast", "shoutcast")
DIRECT_EXTENSIONS = (
    ".mp3",
    ".m4a",
    ".aac",
    ".ogg",
    ".opus",
    ".flac",
    ".wav",
    ".m3u8",
    ".m3u",
    ".pls",
)


class DirectUrlResolver(SourceResolver):
    @staticmethod
    def _has_direct_extension(url: str) -> bool:
        lowered = url.lower()
        return any(ext in lowered for ext in DIRECT_EXTENSIONS)

    @staticmethod
    def _has_stream_hints(url: str) -> bool:
        lowered = url.lower()
        markers = ("live", "stream", "radio", "icecast", "shoutcast", "listen", "mount", "channel")
        return any(marker in lowered for marker in markers)

    @staticmethod
    def _looks_like_stream_host(host: str) -> bool:
        if not host:
            return False
        prefixes = ("radio.", "stream.", "live.", "icecast.", "shoutcast.")
        return host.startswith(prefixes)

    def can_handle_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        host = (parsed.hostname or "").lower()
        for blocked in KNOWN_NON_DIRECT_DOMAINS:
            if host == blocked or host.endswith(f".{blocked}"):
                return False
        normalized = self.normalize_url(url)
        return (
            self._has_direct_extension(normalized)
            or self._has_stream_hints(normalized)
            or self._looks_like_stream_host(host)
        )

    def normalize_url(self, url: str) -> str:
        return url.strip()

    def is_playlist_url(self, url: str) -> bool:
        _ = url
        return False

    def _is_likely_live(self, url: str) -> bool:
        lowered = url.lower()
        return any(marker in lowered for marker in LIVE_MARKERS)

    def _title_from_url(self, url: str) -> str | None:
        parsed = urlparse(url)
        basename = os.path.basename(parsed.path or "").strip()
        if not basename:
            return None
        return basename[:160]

    def resolve_video(self, url: str) -> ResolvedTrack:
        normalized = self.normalize_url(url)
        is_live = self._is_likely_live(normalized)
        return ResolvedTrack(
            source_url=url,
            normalized_url=normalized,
            title=self._title_from_url(normalized),
            channel=source_site_from_url(normalized),
            duration_seconds=None,
            thumbnail_url=None,
            stream_url=normalized,
            source_site=source_site_from_url(normalized),
            is_live=is_live,
            can_seek=not is_live,
        )

    def spawn_audio_stream(self, url: str) -> subprocess.Popen[bytes]:
        _ = url
        raise DirectUrlError("DirectUrlResolver does not spawn yt-dlp streams")

    def preview_playlist(self, url: str) -> PlaylistPreview:
        raise DirectUrlError("Direct URLs do not support playlist preview")

