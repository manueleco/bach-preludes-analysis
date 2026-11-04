# Bach Preludes Analysis

Python toolkit for symbolic and audio-assisted analysis of a curated collection of works by one composer.

Today the main case study is the six Bach cello-suite preludes `BWV 1007-1012`, but the repo is now structured so a future corpus such as Chopin nocturnes can be added with the same workflow.

## Project Intent

- use curated symbolic scores as the source of truth for harmony
- use audio to study expression, tempo, rubato, dynamics, spectral density, and articulation proxies
- compare pieces inside one collection with reproducible metrics
- keep private or copyrighted assets out of GitHub
- document the project so musicians can read the outputs without needing a software background

## Analysis Scope

The symbolic layer currently targets:

- global key and local key regions
- harmonic segments by beat or event
- chord root, quality, inversion, seventh, Roman numeral, and broad harmonic function
- tonicizations and modulation cues
- harmonic rhythm
- cadence heuristics
- secondary dominants and leading-tone functions
- non-chord-tone heuristics
- recurrent progressions and sequence detection
- chromatic and dissonance-density indicators
- basic voice-leading diagnostics

The audio layer currently targets:

- pulse and tempo estimation
- local tempo and rubato
- dynamic range and variability
- spectral centroid, bandwidth, flatness, and flux
- transient density as an articulation proxy
- light score-audio validation through pitch-class similarity

## Core Policy

- For harmony, rely on the curated symbolic corpus.
- For expression, rely on a single-performer private audio corpus.
- For reproducibility, keep manifests, scripts, and public references in git.
- For copyright-sensitive materials, keep local-only assets in case-study private folders.

## Repository Layout

```text
bach-preludes-analysis/
├── data/
│   ├── case_studies/
│   │   └── bach_cello_suites/
│   │       ├── catalog/
│   │       ├── symbolic/
│   │       │   ├── official_curated/
│   │       │   ├── raw_pdfs/
│   │       │   ├── converted/
│   │       │   └── manifests/
│   │       └── audio/
│   │           ├── inbox/
│   │           ├── private_reference/
│   │           └── processed/
│   └── sources/
│       └── symbolic/
├── docs/internal/
├── notebooks/
├── outputs/
├── scripts/
├── src/bach_preludes_analysis/
└── tests/
```

## Public vs Private

Public and reproducible:

- source code
- manifests
- source-profile metadata
- notebook
- curated symbolic corpus when its provenance allows publication

Private or local-only:

- raw PDFs used for OMR
- intermediate Audiveris exports
- private audio recordings such as the Yo-Yo Ma set

These local-only folders are ignored by git.

## Case Study Structure

Each case study should provide:

- a `catalog/pieces.csv`
- an `official_curated` symbolic corpus
- optional raw PDFs and OMR staging
- an audio inbox and, if needed, a private single-interpreter reference corpus

The active Bach catalog lives at:

`data/case_studies/bach_cello_suites/catalog/pieces.csv`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[notebook,audio]"
```

If `Essentia` is compatible with your platform, you can install it separately:

```bash
pip install essentia
```

If not, the project falls back to `librosa`.

## CLI Usage

Describe available case studies:

```bash
python main.py describe-case-studies
```

Describe profiles and availability for the Bach case study:

```bash
python main.py describe-sources --case-study bach_cello_suites
```

Analyze one curated score:

```bash
python main.py analyze \
  --case-study bach_cello_suites \
  --corpus-profile official_curated \
  --input data/case_studies/bach_cello_suites/symbolic/official_curated/suite_01_prelude_g_major_bwv1007.musicxml
```

Analyze the full curated symbolic corpus:

```bash
python main.py analyze-corpus --case-study bach_cello_suites --corpus-profile official_curated
```

Compare all pieces in the active symbolic corpus:

```bash
python main.py compare --case-study bach_cello_suites --corpus-profile official_curated
```

Analyze the curated private audio corpus:

```bash
python main.py analyze-audio-corpus --case-study bach_cello_suites --audio-profile single_interpreter_reference
```

Compare the private audio corpus:

```bash
python main.py compare-audio --case-study bach_cello_suites --audio-profile single_interpreter_reference
```

Validate score/audio pairs across the case study:

```bash
python main.py validate-case-study --case-study bach_cello_suites --backend librosa
```

## Symbolic Preparation

Normalize converted symbolic files into the official curated corpus:

```bash
.venv/bin/python scripts/prepare_case_study_corpus.py \
  --case-study bach_cello_suites \
  --input data/case_studies/bach_cello_suites/symbolic/converted/audiveris
```

## Audio Organization

Move or copy private audio files from the inbox into canonical filenames:

```bash
.venv/bin/python scripts/organize_case_study_audio.py \
  --case-study bach_cello_suites \
  --mode copy
```

## External Symbolic Reference Sources

Populate external source profiles:

```bash
.venv/bin/python scripts/ingest_kern_sources.py
.venv/bin/python scripts/ingest_mutopia_sources.py
.venv/bin/python scripts/ingest_musopen_sources.py
```

These source profiles are for contrast and gap-filling, not for replacing the curated symbolic corpus.

## Notebook

El notebook principal del caso de estudio Bach es:

`notebooks/case_studies/bach_cello_suites/bach_cello_suites_case_study.ipynb`

Ese cuaderno usa especificamente las preguntas musicales del planteamiento inicial del proyecto y las presenta en formato legible para musicos.

`notebooks/bach_preludes_walkthrough.ipynb` queda como ruta legacy de compatibilidad.

## Project Tracking

- live project status: `TODO.md`
- internal architecture and implementation notes: `docs/internal/`

## Important Caveat

For solo-cello repertory, harmony is often implied rather than literally vertical on the page. This toolkit should therefore be read as an explainable analytical assistant, not as a replacement for musical judgment.
