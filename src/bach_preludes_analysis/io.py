from __future__ import annotations

from pathlib import Path

from music21 import converter, stream

from bach_preludes_analysis.config import SUPPORTED_AUDIO_EXTENSIONS, SUPPORTED_SCORE_EXTENSIONS


def discover_score_paths(input_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SCORE_EXTENSIONS
    )


def discover_audio_paths(input_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
    )


def load_score(input_path: Path) -> stream.Score:
    return converter.parse(str(input_path))


def infer_prelude_id(input_path: Path) -> str:
    stem = input_path.stem.lower()
    return stem.replace(" ", "_").replace("-", "_")


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
