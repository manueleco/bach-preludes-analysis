from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from music21 import converter, stream

from bach_preludes_analysis.case_studies import get_case_study
from bach_preludes_analysis.catalog import canonical_piece_id_from_text, catalog_row_for_piece_id
from bach_preludes_analysis.config import DEFAULT_CASE_STUDY_ID, SUPPORTED_SCORE_EXTENSIONS


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare and normalize symbolic score files into the curated corpus of a case study."
    )
    parser.add_argument("--input", required=True, help="A symbolic score file or a directory containing score files.")
    parser.add_argument("--output-dir", help="Directory where normalized files will be written.")
    parser.add_argument("--case-study", default=DEFAULT_CASE_STUDY_ID)
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without writing files.")
    return parser.parse_args()


def _score_label(score: stream.Score, fallback: str) -> str:
    pieces = [
        getattr(score.metadata, "title", None) if score.metadata else None,
        getattr(score.metadata, "movementName", None) if score.metadata else None,
        getattr(score, "movementName", None),
        fallback,
    ]
    return " | ".join(piece for piece in pieces if piece)


def _canonical_filename_from_text(text: str, case_study_id: str) -> str | None:
    piece_id = canonical_piece_id_from_text(text, case_study_id=case_study_id)
    if piece_id is None:
        return None
    row = catalog_row_for_piece_id(piece_id, case_study_id=case_study_id)
    if row is None:
        return None
    return row["canonical_filename"]


def _write_score(score: stream.Score, output_path: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"would write: {output_path}")
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    score.write("musicxml", fp=str(output_path))
    print(f"wrote: {output_path}")


def _copy_file(input_path: Path, output_path: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"would copy: {input_path} -> {output_path}")
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(input_path, output_path)
    print(f"copied: {input_path} -> {output_path}")


def _prepare_single_score(input_path: Path, output_dir: Path, case_study_id: str, dry_run: bool) -> None:
    canonical_name = _canonical_filename_from_text(input_path.name, case_study_id=case_study_id)
    if canonical_name and input_path.suffix.lower() in {".musicxml", ".xml"}:
        _copy_file(input_path, output_dir / canonical_name, dry_run)
        return

    parsed = converter.parse(str(input_path))
    if isinstance(parsed, stream.Opus):
        matched = 0
        for index, score in enumerate(parsed.scores):
            label = _score_label(score, f"{input_path.stem}_{index + 1}")
            canonical_name = _canonical_filename_from_text(label, case_study_id=case_study_id)
            if canonical_name is None:
                continue
            _write_score(score, output_dir / canonical_name, dry_run)
            matched += 1
        if matched == 0:
            print(f"no catalog matches found inside opus: {input_path}")
        return

    if isinstance(parsed, stream.Score):
        label = _score_label(parsed, input_path.stem)
        canonical_name = _canonical_filename_from_text(label, case_study_id=case_study_id)
        if canonical_name is None:
            print(f"could not infer target piece from: {input_path}")
            return
        _write_score(parsed, output_dir / canonical_name, dry_run)
        return

    print(f"unsupported parsed object for: {input_path}")


def main() -> None:
    args = _parse_args()
    case_study = get_case_study(args.case_study)
    input_path = Path(args.input).expanduser().resolve()
    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else case_study.symbolic_curated_dir
    )

    if input_path.is_dir():
        for score_file in sorted(path for path in input_path.iterdir()
                                 if path.is_file() and path.suffix.lower() in SUPPORTED_SCORE_EXTENSIONS):
            _prepare_single_score(score_file, output_dir, case_study.case_study_id, args.dry_run)
        return

    _prepare_single_score(input_path, output_dir, case_study.case_study_id, args.dry_run)


if __name__ == "__main__":
    main()
