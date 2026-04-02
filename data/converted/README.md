# Converted Scores

This folder stores intermediate symbolic material produced automatically from source artifacts.

## Intended Use

- keep OMR exports separate from the final curated corpus
- preserve a staging area for Audiveris outputs, logs, and `.omr` books
- review and clean these files in MuseScore before promoting them into `data/raw/`

## Current Subfolders

- `audiveris/`: batch or GUI-assisted exports from Audiveris such as `.mxl`, `.musicxml`, `.omr`, and processing logs

## Workflow

1. Split source PDFs into `data/raw/pdfs/`.
2. Run Audiveris into `data/converted/audiveris/`.
3. Open those files in MuseScore and correct notation or rhythm issues.
4. Normalize the cleaned results into `data/raw/` with `scripts/prepare_cello_suite_corpus.py`.

## Git Policy

Generated files inside `data/converted/audiveris/` are ignored by git by default.
Keep only the folder structure and documentation in version control unless you intentionally decide otherwise.
