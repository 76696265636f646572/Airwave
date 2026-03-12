"""Resolve per-provider cookie paths for yt-dlp from stored settings."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Callable

NETSCAPE_HEADER = "# Netscape HTTP Cookie File"


def provider_from_url(url: str) -> str | None:
    """Detect provider id from URL. Returns e.g. 'youtube' for youtube.com/youtu.be."""
    if not url:
        return None
    from urllib.parse import urlparse

    parsed = urlparse(url)
    netloc = (parsed.netloc or "").lower()
    if "youtube.com" in netloc or netloc.endswith("youtu.be"):
        return "youtube"
    if "soundcloud.com" in netloc:
        return "soundcloud"
    if "vimeo.com" in netloc:
        return "vimeo"
    return None


def _is_file_path(value: str) -> bool:
    """True if value looks like a file path (single line, path-like)."""
    stripped = value.strip()
    if "\n" in stripped:
        return False
    if stripped.startswith(NETSCAPE_HEADER):
        return False
    # Path-like: absolute or relative with path separators
    return bool(stripped) and (stripped.startswith("/") or "\\" in stripped or (len(stripped) > 1 and stripped[1] == ":"))


def resolve_cookie_path(value: str) -> str | None:
    """
    Resolve cookie value to a file path for yt-dlp --cookies.
    - If value is a file path that exists: return it.
    - If value is Netscape content: write to temp file, return path.
    Returns None if value is empty or invalid.
    """
    if not value or not value.strip():
        return None

    stripped = value.strip()

    if _is_file_path(stripped):
        path = Path(stripped)
        if path.is_file():
            return str(path.resolve())
        return None

    # Treat as Netscape cookie content; write to temp file (not deleted; /tmp is ephemeral)
    try:
        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(stripped)
        return path
    except OSError:
        return None


def create_cookie_resolver(get_setting: Callable[[str], str | None]) -> Callable[[str], str | None]:
    """
    Create a resolver that returns cookie file path for a URL.
    Uses get_setting("cookies:{provider}") to fetch stored value.
    """

    def get_cookie_path_for_url(url: str) -> str | None:
        provider = provider_from_url(url)
        if not provider:
            return None
        key = f"cookies:{provider}"
        value = get_setting(key)
        if not value:
            return None
        return resolve_cookie_path(value)

    return get_cookie_path_for_url
