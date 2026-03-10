from app.services.resolver.base import PlaylistPreview, ResolvedTrack
from app.services.resolver.utils import source_site_from_url, youtube_video_id_from_url
from app.services.resolver.yt_dlp_resolver import YtDlpError, YtDlpResolver

# Backwards compatibility shim: existing imports still reference YtDlpService.
YtDlpService = YtDlpResolver

