#!/bin/zsh

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <raw-pdf-dir> <converted-dir> [audiveris-app-or-bin] [audiveris-home]"
  exit 1
fi

RAW_DIR="$1"
CONVERTED_DIR="$2"
AUDIVERIS_INPUT="${3:-}"
AUDIVERIS_HOME="${4:-./tools/audiveris-home}"
AUDIVERIS_APP=""
SYSTEM_TESSDATA_DIR="${HOME}/Library/Application Support/AudiverisLtd/audiveris/tessdata"

abspath() {
  local target="$1"
  if [[ -d "$target" ]]; then
    (cd "$target" && pwd)
  else
    local dir
    dir="$(dirname "$target")"
    local base
    base="$(basename "$target")"
    (cd "$dir" && printf '%s/%s\n' "$(pwd)" "$base")
  fi
}

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

RAW_DIR="$(abspath "$RAW_DIR")"
CONVERTED_DIR="$(abspath "$CONVERTED_DIR")"
AUDIVERIS_HOME="$(abspath "$AUDIVERIS_HOME")"

if [[ -n "$AUDIVERIS_INPUT" && -d "$AUDIVERIS_INPUT" && "$AUDIVERIS_INPUT" == *.app ]]; then
  AUDIVERIS_APP="$(abspath "$AUDIVERIS_INPUT")"
  AUDIVERIS_BIN="$AUDIVERIS_APP/Contents/MacOS/Audiveris"
else
  AUDIVERIS_BIN="$(resolve_audiveris_bin "$AUDIVERIS_INPUT")"
  if [[ "$AUDIVERIS_BIN" == "./tools/Audiveris.app/Contents/MacOS/Audiveris" ]]; then
    AUDIVERIS_APP="$(abspath "./tools/Audiveris.app")"
  fi
fi

mkdir -p "$CONVERTED_DIR"
mkdir -p "$AUDIVERIS_HOME"

LOCAL_TESSDATA_DIR="$AUDIVERIS_HOME/Library/Application Support/AudiverisLtd/audiveris/tessdata"
if [[ ! -d "$LOCAL_TESSDATA_DIR" ]] && [[ -d "$SYSTEM_TESSDATA_DIR" ]]; then
  mkdir -p "$(dirname "$LOCAL_TESSDATA_DIR")"
  cp -R "$SYSTEM_TESSDATA_DIR" "$LOCAL_TESSDATA_DIR"
fi

for pdf in "$RAW_DIR"/*.pdf; do
  [[ -e "$pdf" ]] || continue
  pdf="$(abspath "$pdf")"
  echo "processing $pdf"
  if [[ -n "$AUDIVERIS_APP" && "$(uname -s)" == "Darwin" ]]; then
    log_prefix="$CONVERTED_DIR/.audiveris_$(basename "${pdf%.*}")"
    rm -f "${log_prefix}.stdout.log" "${log_prefix}.stderr.log"
    open -n -W -j -a "$AUDIVERIS_APP" \
      --env HOME="$AUDIVERIS_HOME" \
      -o "${log_prefix}.stdout.log" \
      --stderr "${log_prefix}.stderr.log" \
      --args -batch -transcribe -export -output "$CONVERTED_DIR" "$pdf"
    [[ -f "${log_prefix}.stdout.log" ]] && cat "${log_prefix}.stdout.log"
    [[ -f "${log_prefix}.stderr.log" ]] && cat "${log_prefix}.stderr.log" >&2
  else
    HOME="$AUDIVERIS_HOME" "$AUDIVERIS_BIN" -batch -transcribe -export -output "$CONVERTED_DIR" "$pdf"
  fi
done
