#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$ROOT_DIR/bin"
TARGET_PATH="${AIRWAVE_SPOTDL_PATH:-$BIN_DIR/spotdl}"
mkdir -p "$(dirname "$TARGET_PATH")"

OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
  Linux) PLATFORM_SUFFIX="linux" ;;
  Darwin) PLATFORM_SUFFIX="darwin" ;;
  *)
    echo "Unsupported OS: $OS" >&2
    exit 1
    ;;
esac

if [[ "$ARCH" != "x86_64" && "$ARCH" != "amd64" && "$ARCH" != "arm64" && "$ARCH" != "aarch64" ]]; then
  echo "Unsupported architecture: $ARCH" >&2
  exit 1
fi

RELEASE_JSON="$(curl -fsSL https://api.github.com/repos/spotDL/spotify-downloader/releases/latest)"
DOWNLOAD_URL="$(
  RELEASE_JSON="$RELEASE_JSON" PLATFORM_SUFFIX="$PLATFORM_SUFFIX" python3 - <<'PY'
import json
import os
import sys

payload = json.loads(os.environ["RELEASE_JSON"])
suffix = "-" + os.environ["PLATFORM_SUFFIX"]
assets = payload.get("assets") or []
for asset in assets:
    name = str(asset.get("name") or "")
    if name.lower().endswith(suffix):
        print(asset.get("browser_download_url") or "")
        sys.exit(0)
sys.exit(1)
PY
)"

if [[ -z "${DOWNLOAD_URL:-}" ]]; then
  echo "Could not locate a spotdl release asset for $OS" >&2
  exit 1
fi

echo "Downloading spotdl from $DOWNLOAD_URL"
curl -fsSL "$DOWNLOAD_URL" -o "$TARGET_PATH"
chmod +x "$TARGET_PATH"
"$TARGET_PATH" --version
echo "Installed spotdl to $TARGET_PATH"
