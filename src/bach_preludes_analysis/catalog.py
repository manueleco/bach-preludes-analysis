from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

from bach_preludes_analysis.case_studies import get_case_study
from bach_preludes_analysis.config import DEFAULT_CASE_STUDY_ID


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


@lru_cache(maxsize=None)
def load_catalog_rows(case_study_id: str = DEFAULT_CASE_STUDY_ID) -> tuple[dict[str, str], ...]:
    catalog_path = get_case_study(case_study_id).catalog_path
    if not catalog_path.exists():
        return tuple()

    with catalog_path.open("r", encoding="utf-8", newline="") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle))


def catalog_row_for_piece_id(piece_id: str, case_study_id: str = DEFAULT_CASE_STUDY_ID) -> dict[str, str] | None:
    for row in load_catalog_rows(case_study_id):
        if row.get("piece_id") == piece_id:
            return row
    return None


def _catalog_match_tokens(row: dict[str, str]) -> list[str]:
    title = row.get("title", "")
    movement_title = row.get("movement_title", "")
    catalog_number = row.get("catalog_number", "")
    tokens = [
        row.get("piece_id", ""),
        Path(row.get("canonical_filename", "")).stem,
        catalog_number,
        f"{title} {movement_title}".strip(),
        f"{catalog_number} {movement_title}".strip(),
    ]
    aliases = row.get("aliases", "")
    if aliases:
        tokens.extend(alias.strip() for alias in aliases.split("|"))
    return [_normalize_text(token) for token in tokens if token]


def canonical_piece_id_from_text(text: str, case_study_id: str = DEFAULT_CASE_STUDY_ID) -> str | None:
    lowered = _normalize_text(text)
    if not lowered:
        return None

    for row in load_catalog_rows(case_study_id):
        for token in _catalog_match_tokens(row):
            if token and f" {token} " in f" {lowered} ":
                return row["piece_id"]
    return None


def catalog_row_for_path(input_path: Path, case_study_id: str = DEFAULT_CASE_STUDY_ID) -> dict[str, str] | None:
    piece_id = canonical_piece_id_from_text(input_path.stem, case_study_id=case_study_id)
    if piece_id is None:
        return None
    return catalog_row_for_piece_id(piece_id, case_study_id=case_study_id)
