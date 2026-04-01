#!/bin/zsh

set -euo pipefail

INSTALL_DIR="${1:-./tools/audiveris}"
MODE="${2:-source}"

mkdir -p "$(dirname "$INSTALL_DIR")"

if [[ "$MODE" == "source" ]]; then
  if [[ -d "$INSTALL_DIR/.git" ]]; then
    echo "Audiveris source already present at $INSTALL_DIR"
    exit 0
  fi
  git clone https://github.com/Audiveris/audiveris "$INSTALL_DIR"
  echo "Cloned Audiveris source into $INSTALL_DIR"
  exit 0
fi

if [[ "$MODE" == "macos-binary" ]]; then
  if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "macos-binary mode only works on macOS"
    exit 1
  fi

  APP_DEST="${INSTALL_DIR}"
  if [[ "$APP_DEST" != *.app ]]; then
    APP_DEST="$APP_DEST/Audiveris.app"
  fi

  TMP_DIR="$(mktemp -d)"
  API_JSON="$TMP_DIR/release.json"

  curl -L "https://api.github.com/repos/Audiveris/audiveris/releases/latest" -o "$API_JSON"
  DMG_URL="$(python3 - <<'PY' "$API_JSON"
import json, sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())
for asset in data.get("assets", []):
    url = asset.get("browser_download_url", "")
    if url.endswith("macosx-arm64.dmg"):
        print(url)
        raise SystemExit(0)
raise SystemExit("No macOS arm64 DMG asset found in latest Audiveris release.")
PY
)"

  DMG_PATH="$TMP_DIR/audiveris.dmg"
  MOUNT_DIR="$TMP_DIR/mount"
  mkdir -p "$MOUNT_DIR"

  curl -L "$DMG_URL" -o "$DMG_PATH"
  printf 'Y\n' | hdiutil attach "$DMG_PATH" -mountpoint "$MOUNT_DIR" -nobrowse
  cp -R "$MOUNT_DIR/Audiveris.app" "$APP_DEST"
  hdiutil detach "$MOUNT_DIR"
  echo "Installed Audiveris.app into $APP_DEST"
  exit 0
fi

echo "Unsupported install mode: $MODE"
echo "Currently supported: source, macos-binary"
exit 1
