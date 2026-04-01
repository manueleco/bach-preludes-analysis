from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

from music21 import converter, stream

CANONICAL_PRELUDES = {
    1007: "suite_01_prelude_g_major_bwv1007.musicxml",
    1008: "suite_02_prelude_d_minor_bwv1008.musicxml",
    1009: "suite_03_prelude_c_major_bwv1009.musicxml",
    1010: "suite_04_prelude_eb_major_bwv1010.musicxml",
    1011: "suite_05_prelude_c_minor_bwv1011.musicxml",
    1012: "suite_06_prelude_d_major_bwv1012.musicxml",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare and normalize MusicXML files for the six Bach cello-suite preludes."
    )
    parser.add_argument("--input", required=True, help="A score file or a directory containing score files.")
    parser.add_argument("--output-dir", required=True, help="Directory where normalized Prelude MusicXML files will be written.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without writing files.")
    return parser.parse_args()


def _canonical_name_from_text(text: str) -> str | None:
    normalized = text.lower()
    match = re.search(r"bwv[\s_-]*(1007|1008|1009|1010|1011|1012)", normalized)
    if not match:
        match = re.search(r"\b(1007|1008|1009|1010|1011|1012)\b", normalized)
    if not match:
        return None
    bwv = int(match.group(1))
    if "prelude" not in normalized and "preludio" not in normalized and "preludium" not in normalized:
        return None
    return CANONICAL_PRELUDES.get(bwv)


def _score_label(score: stream.Score, fallback: str) -> str:
    pieces = [
        getattr(score.metadata, "title", None) if score.metadata else None,
        getattr(score.metadata, "movementName", None) if score.metadata else None,
        getattr(score, "movementName", None),
        fallback,
    ]
    return " | ".join(piece for piece in pieces if piece)


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


def _prepare_single_score(input_path: Path, output_dir: Path, dry_run: bool) -> None:
    canonical_name = _canonical_name_from_text(input_path.name)
    if canonical_name and input_path.suffix.lower() in {".musicxml", ".xml", ".mxl"}:
        _copy_file(input_path, output_dir / canonical_name, dry_run)
        return

    parsed = converter.parse(str(input_path))
    if isinstance(parsed, stream.Opus):
        matched = 0
        for index, score in enumerate(parsed.scores):
            label = _score_label(score, f"{input_path.stem}_{index + 1}")
            canonical_name = _canonical_name_from_text(label)
            if canonical_name is None:
                continue
            _write_score(score, output_dir / canonical_name, dry_run)
            matched += 1
        if matched == 0:
            print(f"no preludes matched inside opus: {input_path}")
        return

    if isinstance(parsed, stream.Score):
        label = _score_label(parsed, input_path.stem)
        canonical_name = _canonical_name_from_text(label)
        if canonical_name is None:
            print(f"could not infer target prelude from: {input_path}")
            return
        _write_score(parsed, output_dir / canonical_name, dry_run)
        return

    print(f"unsupported parsed object for: {input_path}")


def main() -> None:
    args = _parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if input_path.is_dir():
        score_files = sorted(path for path in input_path.iterdir() if path.is_file())
        for score_file in score_files:
            _prepare_single_score(score_file, output_dir, args.dry_run)
        return

    _prepare_single_score(input_path, output_dir, args.dry_run)


if __name__ == "__main__":
    main()
