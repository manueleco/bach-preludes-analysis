# Bach Preludes Analysis

Python toolkit for harmonic and comparative analysis of the six Bach cello-suite preludes, BWV `1007-1012`, using symbolic scores (`MusicXML` or `MIDI`) and, optionally, audio-based features with `Essentia` or a `librosa` fallback backend.

## Goals

- analyze each prelude with a consistent symbolic pipeline
- optionally analyze recordings to extract tempo, metering, tonality, and spectral descriptors
- compare multiple preludes through harmonic, tonal, and voice-leading features
- compare multiple recordings through tempo, dynamic, and spectral profiles
- present results in a way that is readable for musicians, not only developers
- keep the project ready to grow into a richer app or web interface later

## Current Scope

The repository includes a first analysis stack for:

- global key and local key regions
- beat or event-based harmonic segmentation
- chord labels, inversions, sevenths, Roman numerals, and broad harmonic function
- tonicizations and modulation cues
- harmonic rhythm
- cadence heuristics
- secondary dominants and leading-tone chords
- non-chord tone heuristics
- recurrent progressions and sequence detection
- chromatic and dissonance-density indicators
- basic voice-leading diagnostics
- cross-prelude comparison tables and similarity scores

Some categories, especially cadences, non-chord tones, and voice-leading, are implemented as heuristic `v1` analyzers. They are designed to be inspectable and easy to refine as the corpus grows.

Because this corpus is for solo cello, harmony is often implied rather than fully verticalized on the page. That means the project should be read as a symbolic inference tool:

- some tonal and harmonic readings come from local note-grouping heuristics rather than literal simultaneities
- cadence and function labels are best treated as analytical proposals to review musically
- audio and score evidence become especially useful when used together

The audio layer is intentionally complementary. It helps with:

- tempo and pulse estimation from recordings
- loudness and metering summaries
- key estimation from performed audio
- spectral descriptors that can reflect interpretation, articulation, and sonority

It does not replace score-based harmonic analysis. For Roman numerals, harmonic function, cadences, and voice-leading, symbolic input remains the main source of truth.

## Repository Layout

```text
bach-preludes-analysis/
├── data/
│   ├── audio/
│   │   ├── processed/
│   │   └── raw/
│   ├── processed/
│   └── raw/
├── notebooks/
├── outputs/
│   ├── figures/
│   └── reports/
├── src/bach_preludes_analysis/
│   ├── analysis/
│   └── reporting/
└── tests/
```

## Recommended Input

- prefer `MusicXML`, `.mxl`, or `.xml` for the main analyses
- use `MIDI` mainly as a fallback or supplementary source
- keep one file per prelude in `data/raw/`
- use audio files in `data/audio/raw/` when you want to analyze recordings
- preferred audio formats: `WAV`, `FLAC`, `AIFF`; `MP3` is acceptable if needed

Suggested filename pattern:

```text
suite_01_prelude_g_major_bwv1007.musicxml
suite_02_prelude_d_minor_bwv1008.musicxml
suite_03_prelude_c_major_bwv1009.musicxml
suite_04_prelude_eb_major_bwv1010.musicxml
suite_05_prelude_c_minor_bwv1011.musicxml
suite_06_prelude_d_major_bwv1012.musicxml
```

Canonical target list:

`data/raw/cello_suite_manifest.csv`

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[notebook]"
```

If you want audio analysis with Essentia as well:

```bash
pip install -e ".[notebook,audio]"
```

This installs the fallback audio backend based on `librosa`, which is usually easier to get running.

If you also want the `Essentia` backend, install it separately after confirming platform compatibility:

```bash
pip install essentia
```

Depending on your Python version and platform, `Essentia` may need a working compilation toolchain. In this macOS Apple Silicon + Python 3.14 environment, the build failed from source, so the repo keeps it optional and falls back to `librosa`.

## CLI Usage

Analyze one score:

```bash
python main.py analyze --input data/raw/suite_01_prelude_g_major_bwv1007.musicxml
```

Analyze a whole folder:

```bash
python main.py analyze-corpus --input-dir data/raw
```

Compare all detected preludes:

```bash
python main.py compare --input-dir data/raw
```

Analyze one recording:

```bash
python main.py analyze-audio --input data/audio/raw/suite_01_prelude_g_major_bwv1007_reference.wav
```

Analyze an audio folder:

```bash
python main.py analyze-audio-corpus --input-dir data/audio/raw
```

Compare multiple recordings:

```bash
python main.py compare-audio --input-dir data/audio/raw
```

Prepare or normalize a downloaded score corpus:

```bash
.venv/bin/python scripts/prepare_cello_suite_corpus.py --input /path/to/downloads --output-dir data/raw
```

## Notebook

The main notebook lives in `notebooks/bach_preludes_walkthrough.ipynb`.

It is structured as a guided walkthrough so a musician can:

- load one or many preludes
- inspect harmonic labels and tonal regions
- compare cadence profiles, chromatic density, and harmonic rhythm
- read narrative summaries generated from the symbolic analysis

The current notebook focuses on the symbolic workflow first. The audio analysis is available from the CLI and can later be folded into a second notebook or a combined dashboard.

## Data Sources

See `data/raw/README.md` for recommended ways to obtain `MusicXML` and `MIDI` material legally and cleanly.

For recordings, see `data/audio/raw/README.md`.

Current corpus target:

- Suite No. 1 in G major, BWV 1007
- Suite No. 2 in D minor, BWV 1008
- Suite No. 3 in C major, BWV 1009
- Suite No. 4 in E-flat major, BWV 1010
- Suite No. 5 in C minor, BWV 1011
- Suite No. 6 in D major, BWV 1012

The IMSLP collection page for the six suites confirms the scope and also lists public-domain scans and recordings for the set: [IMSLP 6 Cello Suites, BWV 1007-1012](https://imslp.org/wiki/6_Cello_Suites%2C_BWV_1007-1012_%28Bach%2C_Johann_Sebastian%29).

Recommended MusicXML gathering workflow:

1. Use IMSLP as the authoritative work list and editorial reference for the six suites.
2. Search MuseScore for each prelude or for a complete suite collection. Since you already have a MuseScore account and the app installed, this is the most practical route to editable notation.
3. Open the score in MuseScore Studio and export to `MusicXML` or `MXL`. MuseScore officially supports opening and exporting `MusicXML`: [MuseScore file management](https://handbook.musescore.org/fi/file-management).
4. If you get a folder of mixed filenames or a combined export, run `scripts/prepare_cello_suite_corpus.py` to normalize whatever can be matched automatically to the six canonical filenames.
5. Review each exported prelude quickly in MuseScore before analysis, especially slurs, grace notes, tuplets, repeats, and editorial bowings.

## Next Directions

- refine cadence detection with phrase-boundary modeling
- improve non-chord tone labeling with voice-aware context
- align symbolic and audio analyses into a single report per prelude
- add score annotation export back into `MusicXML`
- build an interactive dashboard or lightweight app on top of the same analysis pipeline
