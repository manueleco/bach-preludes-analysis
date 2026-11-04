from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from bach_preludes_analysis.case_studies import get_case_study
from bach_preludes_analysis.catalog import catalog_row_for_piece_id
from bach_preludes_analysis.config import DEFAULT_CASE_STUDY_ID
from bach_preludes_analysis.io import discover_audio_paths, infer_piece_id


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy or move local audio files from an inbox into the canonical private reference folder of a case study."
    )
    parser.add_argument("--input-dir", help="Source folder with audio files.")
    parser.add_argument("--output-dir", help="Target folder for organized audio files.")
    parser.add_argument("--case-study", default=DEFAULT_CASE_STUDY_ID)
    parser.add_argument("--mode", choices=["copy", "move"], default="copy")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _canonical_audio_name(piece_id: str, input_path: Path, case_study_id: str) -> str:
    row = catalog_row_for_piece_id(piece_id, case_study_id=case_study_id)
    stem = piece_id if row is None else Path(row["canonical_filename"]).stem
    return f"{stem}_reference{input_path.suffix.lower()}"


def _transfer(input_path: Path, output_path: Path, mode: str, dry_run: bool) -> None:
    if dry_run:
        print(f"would {mode}: {input_path} -> {output_path}")
        return
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing audio: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if mode == "move":
        shutil.move(str(input_path), str(output_path))
    else:
        shutil.copy2(input_path, output_path)
    print(f"{mode}d: {input_path} -> {output_path}")


def main() -> None:
    args = _parse_args()
    case_study = get_case_study(args.case_study)
    input_dir = Path(args.input_dir).expanduser().resolve() if args.input_dir else case_study.audio_inbox_dir
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else case_study.audio_private_reference_dir

    for audio_path in discover_audio_paths(input_dir):
        piece_id = infer_piece_id(audio_path, case_study_id=case_study.case_study_id)
        if catalog_row_for_piece_id(piece_id, case_study.case_study_id) is None:
            print(f"skipped (unmatched): {audio_path}")
            continue
        target_name = _canonical_audio_name(piece_id, audio_path, case_study.case_study_id)
        _transfer(audio_path, output_dir / target_name, args.mode, args.dry_run)


if __name__ == "__main__":
    main()
