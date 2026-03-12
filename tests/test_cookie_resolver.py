"""Tests for cookie resolver and provider detection."""

import tempfile
from pathlib import Path

import pytest

from app.services.cookie_resolver import (
    NETSCAPE_HEADER,
    create_cookie_resolver,
    provider_from_url,
    resolve_cookie_path,
)


def test_provider_from_url_youtube():
    assert provider_from_url("https://www.youtube.com/watch?v=abc") == "youtube"
    assert provider_from_url("https://youtu.be/abc") == "youtube"
    assert provider_from_url("https://music.youtube.com/watch?v=abc") == "youtube"


def test_provider_from_url_other():
    assert provider_from_url("https://soundcloud.com/artist/track") == "soundcloud"
    assert provider_from_url("https://vimeo.com/123") == "vimeo"


def test_provider_from_url_unknown():
    assert provider_from_url("https://example.com/video") is None
    assert provider_from_url("") is None


def test_resolve_cookie_path_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("# Netscape\ncookie\tline\n")
        path = f.name
    try:
        result = resolve_cookie_path(path)
        assert result == str(Path(path).resolve())
    finally:
        Path(path).unlink(missing_ok=True)


def test_resolve_cookie_path_content():
    content = "# Netscape HTTP Cookie File\n.example.com\t/\tname\tvalue\tTRUE\tFALSE\t0\n"
    result = resolve_cookie_path(content)
    assert result is not None
    assert Path(result).is_file()
    with open(result) as f:
        written = f.read()
    assert written.strip() == content.strip()
    assert NETSCAPE_HEADER in written
    Path(result).unlink(missing_ok=True)


def test_resolve_cookie_path_empty():
    assert resolve_cookie_path("") is None
    assert resolve_cookie_path("   ") is None


def test_create_cookie_resolver():
    settings = {}

    def get_setting(key):
        return settings.get(key)

    resolver = create_cookie_resolver(get_setting)
    assert resolver("https://example.com") is None

    settings["cookies:youtube"] = "# Netscape HTTP Cookie File\n"
    result = resolver("https://www.youtube.com/watch?v=abc")
    assert result is not None
    assert Path(result).is_file()
    Path(result).unlink(missing_ok=True)
