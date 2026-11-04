from __future__ import annotations

import re
from pathlib import Path

from music21 import converter, stream

from bach_preludes_analysis.catalog import canonical_piece_id_from_text
from bach_preludes_analysis.config import DEFAULT_CASE_STUDY_ID, SUPPORTED_AUDIO_EXTENSIONS, SUPPORTED_SCORE_EXTENSIONS


def discover_score_paths(input_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SCORE_EXTENSIONS
    )


def discover_audio_paths(input_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
    )


def load_score(input_path: Path) -> stream.Score:
    return converter.parse(str(input_path))


def infer_piece_id(input_path: Path, case_study_id: str = DEFAULT_CASE_STUDY_ID) -> str:
    canonical_id = canonical_piece_id_from_text(input_path.stem, case_study_id=case_study_id)
    if canonical_id is not None:
        return canonical_id

    stem = input_path.stem.lower()
    slug = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    return slug or "unknown_piece"


def infer_prelude_id(input_path: Path, case_study_id: str = DEFAULT_CASE_STUDY_ID) -> str:
    return infer_piece_id(input_path, case_study_id=case_study_id)


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
