#!/bin/zsh

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <input-pdf> <output-dir>"
  exit 1
fi

INPUT_PDF="$1"
OUTPUT_DIR="$2"

mkdir -p "$OUTPUT_DIR"

# These ranges target the Yokoyama "without slurs" edition from IMSLP.
# They isolate the six preludes only and are much cleaner for OMR than the
# earlier Klengel scan, but they should still be reviewed musically.
declare -a NAMES=(
  "suite_01_prelude_g_major_bwv1007_raw.pdf"
  "suite_02_prelude_d_minor_bwv1008_raw.pdf"
  "suite_03_prelude_c_major_bwv1009_raw.pdf"
  "suite_04_prelude_eb_major_bwv1010_raw.pdf"
  "suite_05_prelude_c_minor_bwv1011_raw.pdf"
  "suite_06_prelude_d_major_bwv1012_raw.pdf"
)

declare -a RANGES=(
  "6-7"
  "12-13"
  "20-21"
  "30-31"
  "40-43"
  "49-51"
)

for idx in {1..6}; do
  range="${RANGES[$idx]}"
  name="${NAMES[$idx]}"
  start_page="${range%-*}"
  end_page="${range#*-}"
  pdfseparate -f "$start_page" -l "$end_page" "$INPUT_PDF" "$OUTPUT_DIR/.tmp_%02d.pdf"
  pdfunite "$OUTPUT_DIR"/.tmp_*.pdf "$OUTPUT_DIR/$name"
  rm "$OUTPUT_DIR"/.tmp_*.pdf
  echo "wrote $OUTPUT_DIR/$name from pages $range"
done
