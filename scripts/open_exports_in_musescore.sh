#!/bin/zsh

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <exports-dir> [app-name]"
  exit 1
fi

EXPORTS_DIR="$1"
APP_NAME="${2:-MuseScore Studio}"

for score in "$EXPORTS_DIR"/*.mxl "$EXPORTS_DIR"/*.musicxml "$EXPORTS_DIR"/*.xml; do
  [[ -e "$score" ]] || continue
  open -a "$APP_NAME" "$score"
done
