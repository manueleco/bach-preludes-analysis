# Raw Score Inputs

Place your source scores here.

## Preferred Formats

- `MusicXML` or compressed `MXL`
- `XML` exported from notation software
- `MIDI` only as fallback when no better symbolic format is available

## Naming Convention

Use clear and stable names so reports remain readable:

```text
suite_01_prelude_g_major_bwv1007.musicxml
suite_02_prelude_d_minor_bwv1008.musicxml
suite_03_prelude_c_major_bwv1009.musicxml
suite_04_prelude_eb_major_bwv1010.musicxml
suite_05_prelude_c_minor_bwv1011.musicxml
suite_06_prelude_d_major_bwv1012.musicxml
```

## Source Hygiene

- prefer editions with clean bowings, articulations, and correct enharmonic spelling
- keep one file per piece
- avoid scanned PDFs converted automatically unless you verify them measure by measure
- if you export from MuseScore, prefer `MusicXML` over `MIDI`
- remember that these preludes are mostly solo-cello textures, so harmonic analysis is often an inference from unfolding lines and broken chords

## Suggested Sources

- IMSLP collection page for the six suites: [IMSLP BWV 1007-1012](https://imslp.org/wiki/6_Cello_Suites%2C_BWV_1007-1012_%28Bach%2C_Johann_Sebastian%29)
- manuscript-based or early printed editions are useful as references, but `MusicXML` will usually need to come from notation exports or carefully prepared transcriptions
- the local PDF `IMSLP36902-PMLP04291-Bach-BWV1007-1012klengel.pdf` can serve as an editorial reference, but a PDF alone is not ideal as the main machine-readable source
- the Yokoyama `without slurs` PDF is a better OMR starting point when you need to work from PDF: `IMSLP268080-PMLP04291-Bach_6_Cello_Suites_without_slurs_Yokoyama_2013.pdf`

## Suggested Workflow

1. collect or export the scores
2. if they come from OMR, stage them first in `data/converted/audiveris/`
3. normalize filenames
4. copy only the curated analysis-ready files into this folder
5. run `python main.py analyze-corpus --input-dir data/raw`

## Practical Route To The Six MusicXML Files

1. Use IMSLP as the authoritative checklist for BWV `1007-1012`.
2. If you only have a scan PDF, split it with:

```bash
zsh scripts/split_cello_suite_pdf.sh "/path/to/IMSLP268080-PMLP04291-Bach_6_Cello_Suites_without_slurs_Yokoyama_2013.pdf" data/raw/pdfs
```

3. Send those PDFs to Audiveris with:

```bash
zsh scripts/process_raw_pdfs_with_audiveris.sh data/raw/pdfs data/converted/audiveris ./tools/Audiveris.app
```

4. Open and clean the generated files in MuseScore Studio from `data/converted/audiveris/`.
5. Normalize filenames with:

```bash
.venv/bin/python scripts/prepare_cello_suite_corpus.py --input data/converted/audiveris --output-dir data/raw
```

6. Compare the resulting files against `data/raw/cello_suite_manifest.csv`.

The Audiveris processing script sets a local `HOME` automatically so the OMR run does not depend on writing into your macOS user Library folders.
When you pass `./tools/Audiveris.app` on macOS, the wrapper launches the app bundle for you instead of requiring the internal executable path.
If Audiveris languages already exist in your user Library, the wrapper copies that `tessdata` into the repo-local Audiveris home automatically.
The current preferred PDF source is the Yokoyama `without slurs` edition, because it gives cleaner prelude-only cuts and is a better candidate for OMR than the earlier scan.

## Why This Matters

For these solo-cello preludes, small notation details can change the analysis:

- slurs and beaming affect segmentation heuristics
- double stops and implied bass notes matter for harmonic inference
- repeats and editorial readings can alter cadence counts and tonal regions
