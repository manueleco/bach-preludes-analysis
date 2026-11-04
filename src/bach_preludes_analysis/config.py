from __future__ import annotations

import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PACKAGE_ROOT.parent
PROJECT_ROOT = SRC_ROOT.parent

DATA_DIR = PROJECT_ROOT / "data"
DATA_CASE_STUDIES_DIR = DATA_DIR / "case_studies"
DATA_SOURCES_DIR = DATA_DIR / "sources"
DATA_SOURCES_SYMBOLIC_DIR = DATA_SOURCES_DIR / "symbolic"
DATA_SOURCES_SYMBOLIC_KERN_DIR = DATA_SOURCES_SYMBOLIC_DIR / "kern"
DATA_SOURCES_SYMBOLIC_MUTOPIA_DIR = DATA_SOURCES_SYMBOLIC_DIR / "mutopia"
DATA_SOURCES_SYMBOLIC_MUSOPEN_DIR = DATA_SOURCES_SYMBOLIC_DIR / "musopen"
DATA_SOURCES_AUDIO_DIR = DATA_SOURCES_DIR / "audio"
DATA_PROCESSED_DIR = DATA_DIR / "processed"

DEFAULT_CASE_STUDY_ID = "bach_cello_suites"
DEFAULT_CASE_STUDY_DIR = DATA_CASE_STUDIES_DIR / DEFAULT_CASE_STUDY_ID

# Compatibility aliases while the repo evolves from a single corpus into a
# reusable collection-analysis toolkit.
DATA_RAW_DIR = DEFAULT_CASE_STUDY_DIR / "symbolic" / "official_curated"
DATA_CONVERTED_DIR = DEFAULT_CASE_STUDY_DIR / "symbolic" / "converted"
DATA_CONVERTED_AUDIVERIS_DIR = DATA_CONVERTED_DIR / "audiveris"
DATA_AUDIO_DIR = DEFAULT_CASE_STUDY_DIR / "audio"
DATA_AUDIO_RAW_DIR = DATA_AUDIO_DIR / "inbox"
DATA_AUDIO_PRIVATE_REFERENCE_DIR = DATA_AUDIO_DIR / "private_reference"
DATA_SOURCES_AUDIO_SINGLE_INTERPRETER_DIR = DATA_AUDIO_PRIVATE_REFERENCE_DIR
DATA_AUDIO_PROCESSED_DIR = DATA_AUDIO_DIR / "processed"

OUTPUT_REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
OUTPUT_FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"
CACHE_DIR = PROJECT_ROOT / ".cache"
MATPLOTLIB_CONFIG_DIR = CACHE_DIR / "matplotlib"

MATPLOTLIB_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MATPLOTLIB_CONFIG_DIR))

SUPPORTED_SCORE_EXTENSIONS = {
    ".krn",
    ".mid",
    ".midi",
    ".mxl",
    ".musicxml",
    ".xml",
}

SUPPORTED_AUDIO_EXTENSIONS = {
    ".aif",
    ".aiff",
    ".flac",
    ".m4a",
    ".mp3",
    ".ogg",
    ".wav",
}

DEFAULT_SEGMENTATION = "beat"
DEFAULT_KEY_WINDOW_MEASURES = 4
