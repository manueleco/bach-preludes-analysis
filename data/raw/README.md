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

## Suggested Workflow

1. collect or export the scores
2. normalize filenames
3. copy them into this folder
4. run `python main.py analyze-corpus --input-dir data/raw`

## Practical Route To The Six MusicXML Files

1. Use IMSLP as the authoritative checklist for BWV `1007-1012`.
2. If you only have a scan PDF, split it with:

```bash
zsh scripts/split_cello_suite_pdf.sh "/path/to/IMSLP36902-PMLP04291-Bach-BWV1007-1012klengel.pdf" data/raw/pdfs
```

3. Send those PDFs to Audiveris with:

```bash
zsh scripts/process_raw_pdfs_with_audiveris.sh data/raw/pdfs data/raw/downloads ./tools/Audiveris.app
```

4. Open and clean the generated files in MuseScore Studio.
5. Normalize filenames with:

```bash
.venv/bin/python scripts/prepare_cello_suite_corpus.py --input /path/to/exports --output-dir data/raw
```

6. Compare the resulting files against `data/raw/cello_suite_manifest.csv`.

The Audiveris processing script sets a local `HOME` automatically so the OMR run does not depend on writing into your macOS user Library folders.
When you pass `./tools/Audiveris.app` on macOS, the wrapper launches the app bundle for you instead of requiring the internal executable path.
With the current Klengel scan, Audiveris is installing and opening correctly here, but the batch transcription still fails during sheet processing, so expect to inspect `.omr` results manually before you count on exported `MusicXML`.

## Why This Matters

For these solo-cello preludes, small notation details can change the analysis:

- slurs and beaming affect segmentation heuristics
- double stops and implied bass notes matter for harmonic inference
- repeats and editorial readings can alter cadence counts and tonal regions
