#!/bin/zsh

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <input-pdf> [raw-dir] [exports-dir] [audiveris-app-or-bin] [musescore-app-name]"
  exit 1
fi

INPUT_PDF="$1"
RAW_DIR="${2:-data/raw/pdfs}"
EXPORTS_DIR="${3:-data/raw/downloads}"
AUDIVERIS_BIN="${4:-./tools/Audiveris.app}"
MUSESCORE_APP_NAME="${5:-MuseScore Studio}"

zsh scripts/split_cello_suite_pdf.sh "$INPUT_PDF" "$RAW_DIR"
zsh scripts/process_raw_pdfs_with_audiveris.sh "$RAW_DIR" "$EXPORTS_DIR" "$AUDIVERIS_BIN"
zsh scripts/open_exports_in_musescore.sh "$EXPORTS_DIR" "$MUSESCORE_APP_NAME"
