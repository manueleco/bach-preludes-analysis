from __future__ import annotations

import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PACKAGE_ROOT.parent
PROJECT_ROOT = SRC_ROOT.parent

DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_AUDIO_RAW_DIR = PROJECT_ROOT / "data" / "audio" / "raw"
DATA_AUDIO_PROCESSED_DIR = PROJECT_ROOT / "data" / "audio" / "processed"
OUTPUT_REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"
OUTPUT_FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"
CACHE_DIR = PROJECT_ROOT / ".cache"
MATPLOTLIB_CONFIG_DIR = CACHE_DIR / "matplotlib"

MATPLOTLIB_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MATPLOTLIB_CONFIG_DIR))

SUPPORTED_SCORE_EXTENSIONS = {
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
