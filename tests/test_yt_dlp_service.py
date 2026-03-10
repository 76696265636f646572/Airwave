"""Tests for YtDlpService URL detection (no subprocess)."""

import pytest

from app.services.yt_dlp_service import YtDlpService


@pytest.fixture
def service():
    return YtDlpService(binary_path="/bin/echo")


def test_is_playlist_url_playlist_page(service):
    assert service.is_playlist_url("https://www.youtube.com/playlist?list=PLxxx") is True
    assert service.is_playlist_url("https://youtube.com/playlist?list=ABC") is True


def test_is_playlist_url_watch_single_video(service):
    assert service.is_playlist_url("https://www.youtube.com/watch?v=Hjw86NcG8Bo") is False


def test_is_playlist_url_watch_with_list_param_treated_as_single_video(service):
    """watch?v=...&list=... should queue/play only the video, not the full playlist."""
    url = "https://www.youtube.com/watch?v=Hjw86NcG8Bo&list=PLMmqTuUsDkRIZ1C1T2AsVz5XIxtVDfSOe"
    assert service.is_playlist_url(url) is False


def test_is_playlist_url_soundcloud_sets_page(service):
    assert service.is_playlist_url("https://soundcloud.com/user/sets/chill-mix") is True


def test_is_playlist_url_vimeo_showcase_page(service):
    assert service.is_playlist_url("https://vimeo.com/showcase/123456") is True


def test_is_playlist_url_youtube_custom_channel_page(service):
    assert service.is_playlist_url("https://www.youtube.com/testchannel") is True
