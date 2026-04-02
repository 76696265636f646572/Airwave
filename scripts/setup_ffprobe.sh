#!/usr/bin/env bash
# Install static ffprobe from https://ffmpeg.martin-riedl.de/
#
# Primary: official "Scripting URLs" redirect (see index → "Scripting URLs"):
#   https://ffmpeg.martin-riedl.de/redirect/latest/{linux|macos}/{amd64|arm64}/release/ffprobe.zip
# Fallback: fetch the homepage HTML and parse the release FFprobe (ZIP) link for this OS/arch.
#
# Env:
#   AIRWAVE_FFPROBE_PATH      — install location (default: <repo>/bin/ffprobe)
#   AIRWAVE_FFPROBE_INDEX_URL — override index page for parsing fallback (default: https://ffmpeg.martin-riedl.de/)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$ROOT_DIR/bin"
TARGET_PATH="${AIRWAVE_FFPROBE_PATH:-$BIN_DIR/ffprobe}"
INDEX_URL="${AIRWAVE_FFPROBE_INDEX_URL:-https://ffmpeg.martin-riedl.de/}"
mkdir -p "$(dirname "$TARGET_PATH")"

if command -v "$TARGET_PATH" >/dev/null 2>&1; then
  echo "ffprobe already present at $TARGET_PATH"
  exit 0
fi

ARCH="$(uname -m)"
OS="$(uname -s)"
case "$OS" in
  Linux) MR_OS="linux" ;;
  Darwin) MR_OS="macos" ;;
  *)
    echo "Unsupported OS: $OS" >&2
    exit 1
    ;;
esac
case "$ARCH" in
  x86_64|amd64) MR_ARCH="amd64" ;;
  aarch64|arm64) MR_ARCH="arm64" ;;
  *)
    echo "Unsupported architecture: $ARCH" >&2
    exit 1
    ;;
esac

# Parse release section of index HTML; print first absolute ffprobe.zip URL for $MR_OS / $MR_ARCH.
ffprobe_zip_url_from_index() {
  local index release rel
  index="$(curl -fsSL "$INDEX_URL")"
  release="$(printf '%s\n' "$index" | sed -n '/<h2>Download Release Build<\/h2>/,/<h2>Timeline/p')"
  rel="$(printf '%s\n' "$release" | grep -oE "href=\"(/download/${MR_OS}/${MR_ARCH}/[^\"]+ffprobe\\.zip)\"" | head -n 1 | sed 's/^href="//;s/".*$//')"
  if [[ -z "${rel:-}" ]]; then
    echo "Could not find ffprobe.zip link for ${MR_OS}/${MR_ARCH} in release section of ${INDEX_URL}" >&2
    return 1
  fi
  if [[ "$rel" == http* ]]; then
    printf '%s\n' "$rel"
  else
    # href is site-relative
    local base="${INDEX_URL%/}"
    printf '%s%s\n' "$base" "$rel"
  fi
}

REDIRECT_URL="https://ffmpeg.martin-riedl.de/redirect/latest/${MR_OS}/${MR_ARCH}/release/ffprobe.zip"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

download_and_install() {
  local url="$1"
  echo "Downloading ffprobe from ${url}"
  rm -f "$TMP_DIR/ffprobe.zip"
  rm -rf "$TMP_DIR/extract"
  mkdir -p "$TMP_DIR/extract"
  if curl -fsSL -L --retry 3 --retry-delay 2 "$url" -o "$TMP_DIR/ffprobe.zip"; then
    unzip -q "$TMP_DIR/ffprobe.zip" -d "$TMP_DIR/extract"
    local ffprobe_bin
    ffprobe_bin="$(find "$TMP_DIR/extract" -type f \( -name ffprobe -o -name ffprobe.exe \) | head -n 1)"
    if [[ -z "${ffprobe_bin:-}" ]]; then
      echo "Could not find ffprobe binary inside zip" >&2
      return 1
    fi
    cp "$ffprobe_bin" "$TARGET_PATH"
    chmod +x "$TARGET_PATH"
    "$TARGET_PATH" -version | head -n 1
    echo "Installed ffprobe to $TARGET_PATH"
    return 0
  fi
  return 1
}

if download_and_install "$REDIRECT_URL"; then
  exit 0
fi

echo "Redirect download failed, trying parsed index URL…" >&2
if ! PARSED_URL="$(ffprobe_zip_url_from_index)"; then
  echo "Failed to resolve ffprobe.zip from ${INDEX_URL}" >&2
  exit 1
fi

if ! download_and_install "$PARSED_URL"; then
  echo "Download failed for ${PARSED_URL}" >&2
  exit 1
fi
