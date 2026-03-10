from __future__ import annotations

from urllib.parse import parse_qs, urlparse


def youtube_video_id_from_url(url: str) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    if host.endswith("youtu.be"):
        return (parsed.path or "").strip("/") or None
    if "youtube.com" in host and "watch" in parsed.path:
        query = parse_qs(parsed.query)
        return (query.get("v") or [None])[0]
    return None


def is_youtube_url(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    return "youtube.com" in host or host.endswith("youtu.be")


def source_site_from_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    if not host:
        return None
    if host.startswith("www."):
        host = host[4:]
    mapping = {
        "youtube.com": "YouTube",
        "youtu.be": "YouTube",
        "soundcloud.com": "SoundCloud",
        "vimeo.com": "Vimeo",
        "twitch.tv": "Twitch",
        "mixcloud.com": "Mixcloud",
    }
    for domain, label in mapping.items():
        if host == domain or host.endswith(f".{domain}"):
            return label
    root = host.split(":")[0]
    if "." in root:
        return root.split(".")[0].capitalize()
    return root.capitalize()


def is_likely_live_url(url: str | None) -> bool:
    if not url:
        return False
    lowered = url.lower()
    markers = ("live", "stream", "radio", ".m3u8", "icecast", "shoutcast", "icy")
    return any(marker in lowered for marker in markers)


def sanitize_yt_dlp_error(message: str) -> str:
    if not message:
        return "Could not process URL"
    cleaned = message.strip().replace("\r", "")
    lowered = cleaned.lower()
    common = {
        "private video": "This media is private",
        "video unavailable": "This media is unavailable",
        "not available in your country": "This media is not available in your region",
        "unsupported url": "This URL is not supported",
    }
    for needle, user_text in common.items():
        if needle in lowered:
            return user_text
    first_line = cleaned.split("\n")[0]
    if len(first_line) > 220:
        first_line = f"{first_line[:217]}..."
    return first_line

