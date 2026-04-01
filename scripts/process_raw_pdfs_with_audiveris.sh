#!/bin/zsh

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <raw-pdf-dir> <output-dir> [audiveris-app-or-bin] [audiveris-home]"
  exit 1
fi

RAW_DIR="$1"
OUTPUT_DIR="$2"
AUDIVERIS_INPUT="${3:-}"
AUDIVERIS_HOME="${4:-./tools/audiveris-home}"
AUDIVERIS_APP=""

resolve_audiveris_bin() {
  local candidate="${1:-}"

  if [[ -z "$candidate" ]]; then
    if [[ -x "./tools/Audiveris.app/Contents/MacOS/Audiveris" ]]; then
      echo "./tools/Audiveris.app/Contents/MacOS/Audiveris"
      return 0
    fi
    if [[ -x "./tools/audiveris/bin/Audiveris" ]]; then
      echo "./tools/audiveris/bin/Audiveris"
      return 0
    fi
    if command -v Audiveris >/dev/null 2>&1; then
      command -v Audiveris
      return 0
    fi
    echo "Could not find Audiveris. Install it first or pass the app or executable path."
    return 1
  fi

  if [[ -d "$candidate" && "$candidate" == *.app ]]; then
    candidate="$candidate/Contents/MacOS/Audiveris"
  fi

  if [[ -x "$candidate" ]]; then
    echo "$candidate"
    return 0
  fi

  echo "Audiveris path is not executable: $candidate"
  return 1
}

if [[ -n "$AUDIVERIS_INPUT" && -d "$AUDIVERIS_INPUT" && "$AUDIVERIS_INPUT" == *.app ]]; then
  AUDIVERIS_APP="$AUDIVERIS_INPUT"
  AUDIVERIS_BIN="$AUDIVERIS_INPUT/Contents/MacOS/Audiveris"
else
  AUDIVERIS_BIN="$(resolve_audiveris_bin "$AUDIVERIS_INPUT")"
  if [[ "$AUDIVERIS_BIN" == "./tools/Audiveris.app/Contents/MacOS/Audiveris" ]]; then
    AUDIVERIS_APP="./tools/Audiveris.app"
  fi
fi

mkdir -p "$OUTPUT_DIR"
mkdir -p "$AUDIVERIS_HOME"

for pdf in "$RAW_DIR"/*.pdf; do
  [[ -e "$pdf" ]] || continue
  echo "processing $pdf"
  if [[ -n "$AUDIVERIS_APP" && "$(uname -s)" == "Darwin" ]]; then
    open -n -W -j -a "$AUDIVERIS_APP" \
      --env HOME="$AUDIVERIS_HOME" \
      -o /dev/stdout \
      --stderr /dev/stderr \
      --args -batch -transcribe -export -output "$OUTPUT_DIR" "$pdf"
  else
    HOME="$AUDIVERIS_HOME" "$AUDIVERIS_BIN" -batch -transcribe -export -output "$OUTPUT_DIR" "$pdf"
  fi
done
