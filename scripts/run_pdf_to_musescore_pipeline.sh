#!/bin/zsh

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <input-pdf> [raw-dir] [converted-dir] [audiveris-app-or-bin] [musescore-app-name]"
  exit 1
fi

INPUT_PDF="$1"
RAW_DIR="${2:-data/raw/pdfs}"
CONVERTED_DIR="${3:-data/converted/audiveris}"
AUDIVERIS_BIN="${4:-./tools/Audiveris.app}"
MUSESCORE_APP_NAME="${5:-MuseScore Studio}"

zsh scripts/split_cello_suite_pdf.sh "$INPUT_PDF" "$RAW_DIR"
zsh scripts/process_raw_pdfs_with_audiveris.sh "$RAW_DIR" "$CONVERTED_DIR" "$AUDIVERIS_BIN"
zsh scripts/open_exports_in_musescore.sh "$CONVERTED_DIR" "$MUSESCORE_APP_NAME"
