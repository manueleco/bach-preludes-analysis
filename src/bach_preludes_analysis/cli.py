from __future__ import annotations

import argparse
import json
from pathlib import Path

from tabulate import tabulate

from bach_preludes_analysis.audio_pipeline import (
    analyze_and_save_audio_corpus,
    analyze_audio,
    analyze_audio_corpus,
    save_audio_analysis,
    save_audio_comparison,
)
from bach_preludes_analysis.case_studies import build_case_study_rows, get_case_study
from bach_preludes_analysis.config import DEFAULT_CASE_STUDY_ID, OUTPUT_FIGURES_DIR, OUTPUT_REPORTS_DIR
from bach_preludes_analysis.comparison import compare_analyses, compare_audio_analyses
from bach_preludes_analysis.corpus_profiles import (
    ANALYSIS_POLICY,
    build_availability_rows,
    build_profile_rows,
    build_reliability_rows,
    resolve_audio_input_dir,
    resolve_symbolic_input_dir,
)
from bach_preludes_analysis.pipeline import (
    analyze_and_save_corpus,
    analyze_corpus,
    analyze_score,
    save_analysis,
    save_comparison,
)
from bach_preludes_analysis.reporting.visuals import plot_harmonic_activity, plot_similarity_heatmap, plot_tonal_timeline
from bach_preludes_analysis.validation import save_validations, validate_case_study_pairs, validate_score_against_audio


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze symbolic scores and recordings for a composer-focused collection case study."
    )
    subparsers = parser.add_subparsers(dest="command")

    cases_parser = subparsers.add_parser("describe-case-studies", help="Describe available case studies.")
    cases_parser.add_argument("--format", choices=["table", "json"], default="table")

    sources_parser = subparsers.add_parser("describe-sources", help="Describe symbolic and audio corpus profiles.")
    sources_parser.add_argument("--format", choices=["table", "json"], default="table")
    sources_parser.add_argument("--case-study", default=DEFAULT_CASE_STUDY_ID)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a single score file.")
    analyze_parser.add_argument("--input", required=True, help="Path to a symbolic score file.")
    analyze_parser.add_argument("--segmentation", choices=["beat", "event"], default="beat")
    analyze_parser.add_argument("--corpus-profile", default="official_curated")
    analyze_parser.add_argument("--case-study", default=DEFAULT_CASE_STUDY_ID)
    analyze_parser.add_argument("--output-dir", default=str(OUTPUT_REPORTS_DIR))
    analyze_parser.add_argument("--figures-dir", default=str(OUTPUT_FIGURES_DIR))

    corpus_parser = subparsers.add_parser("analyze-corpus", help="Analyze all score files in a folder.")
    corpus_parser.add_argument("--input-dir", help="Directory with score files. Defaults to the profile root.")
    corpus_parser.add_argument("--segmentation", choices=["beat", "event"], default="beat")
    corpus_parser.add_argument("--corpus-profile", default="official_curated")
    corpus_parser.add_argument("--case-study", default=DEFAULT_CASE_STUDY_ID)
    corpus_parser.add_argument("--output-dir", default=str(OUTPUT_REPORTS_DIR))

    compare_parser = subparsers.add_parser("compare", help="Compare all score files in a folder.")
    compare_parser.add_argument("--input-dir", help="Directory with score files. Defaults to the profile root.")
    compare_parser.add_argument("--segmentation", choices=["beat", "event"], default="beat")
    compare_parser.add_argument("--corpus-profile", default="official_curated")
    compare_parser.add_argument("--case-study", default=DEFAULT_CASE_STUDY_ID)
    compare_parser.add_argument("--output-dir", default=str(OUTPUT_REPORTS_DIR))
    compare_parser.add_argument("--figures-dir", default=str(OUTPUT_FIGURES_DIR))

    analyze_audio_parser = subparsers.add_parser("analyze-audio", help="Analyze a single audio file.")
    analyze_audio_parser.add_argument("--input", required=True, help="Path to an audio file such as WAV, FLAC, MP3, or AIFF.")
    analyze_audio_parser.add_argument("--backend", choices=["auto", "essentia", "librosa"], default="auto")
    analyze_audio_parser.add_argument("--audio-profile", default="single_interpreter_reference")
    analyze_audio_parser.add_argument("--case-study", default=DEFAULT_CASE_STUDY_ID)
    analyze_audio_parser.add_argument("--output-dir", default=str(OUTPUT_REPORTS_DIR / "audio"))

    corpus_audio_parser = subparsers.add_parser("analyze-audio-corpus", help="Analyze all audio files in a folder.")
    corpus_audio_parser.add_argument("--input-dir", help="Directory with audio files. Defaults to the profile root.")
    corpus_audio_parser.add_argument("--backend", choices=["auto", "essentia", "librosa"], default="auto")
    corpus_audio_parser.add_argument("--audio-profile", default="single_interpreter_reference")
    corpus_audio_parser.add_argument("--case-study", default=DEFAULT_CASE_STUDY_ID)
    corpus_audio_parser.add_argument("--output-dir", default=str(OUTPUT_REPORTS_DIR / "audio"))

    compare_audio_parser = subparsers.add_parser("compare-audio", help="Compare all audio files in a folder.")
    compare_audio_parser.add_argument("--input-dir", help="Directory with audio files. Defaults to the profile root.")
    compare_audio_parser.add_argument("--backend", choices=["auto", "essentia", "librosa"], default="auto")
    compare_audio_parser.add_argument("--audio-profile", default="single_interpreter_reference")
    compare_audio_parser.add_argument("--case-study", default=DEFAULT_CASE_STUDY_ID)
    compare_audio_parser.add_argument("--output-dir", default=str(OUTPUT_REPORTS_DIR / "audio"))

    validate_parser = subparsers.add_parser("validate-score-audio", help="Validate one symbolic score against one audio file.")
    validate_parser.add_argument("--score", required=True)
    validate_parser.add_argument("--audio", required=True)
    validate_parser.add_argument("--backend", choices=["auto", "essentia", "librosa"], default="auto")
    validate_parser.add_argument("--audio-profile", default="single_interpreter_reference")
    validate_parser.add_argument("--case-study", default=DEFAULT_CASE_STUDY_ID)

    validate_case_parser = subparsers.add_parser(
        "validate-case-study",
        help="Validate score/audio pairs for a case study by matching canonical piece ids.",
    )
    validate_case_parser.add_argument("--symbolic-input-dir")
    validate_case_parser.add_argument("--audio-input-dir")
    validate_case_parser.add_argument("--symbolic-profile", default="official_curated")
    validate_case_parser.add_argument("--audio-profile", default="single_interpreter_reference")
    validate_case_parser.add_argument("--backend", choices=["auto", "essentia", "librosa"], default="auto")
    validate_case_parser.add_argument("--case-study", default=DEFAULT_CASE_STUDY_ID)
    validate_case_parser.add_argument("--output-dir", default=str(OUTPUT_REPORTS_DIR / "validation"))
    return parser


def _path_or_none(value: str | None) -> Path | None:
    return Path(value) if value else None


def _print_case_studies_table() -> None:
    print(tabulate(build_case_study_rows(), headers="keys", tablefmt="github"))


def _print_sources_table(case_study_id: str) -> None:
    case_study = get_case_study(case_study_id)
    symbolic_rows = build_profile_rows("symbolic", case_study_id=case_study_id)
    audio_rows = build_profile_rows("audio", case_study_id=case_study_id)
    availability_rows = build_availability_rows(case_study_id=case_study_id)

    print(f"Case study: {case_study.label}")
    print(f"Composer: {case_study.composer}")
    print(f"Collection: {case_study.collection_title}")
    print()
    print("Analysis policy:")
    for index, line in enumerate(ANALYSIS_POLICY, start=1):
        print(f"{index}. {line}")
    print()
    print("Symbolic profiles:")
    print(tabulate(symbolic_rows, headers="keys", tablefmt="github"))
    print()
    print("Audio profiles:")
    print(tabulate(audio_rows, headers="keys", tablefmt="github"))
    print()
    print("Availability snapshot:")
    print(tabulate(availability_rows, headers="keys", tablefmt="github"))
    print()
    print("Reliability details:")
    for profile_row in symbolic_rows + audio_rows:
        rows = build_reliability_rows(profile_row["profile_id"], case_study_id=case_study_id)
        print(profile_row["profile_id"])
        print(tabulate(rows, headers="keys", tablefmt="github"))
        print()


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "describe-case-studies":
        rows = build_case_study_rows()
        if args.format == "json":
            print(json.dumps(rows, indent=2))
            return
        _print_case_studies_table()
        return

    if args.command == "describe-sources":
        if args.format == "json":
            payload = {
                "case_study": build_case_study_rows(),
                "analysis_policy": ANALYSIS_POLICY,
                "symbolic_profiles": build_profile_rows("symbolic", case_study_id=args.case_study),
                "audio_profiles": build_profile_rows("audio", case_study_id=args.case_study),
                "availability": build_availability_rows(case_study_id=args.case_study),
                "reliability": {
                    profile["profile_id"]: build_reliability_rows(profile["profile_id"], case_study_id=args.case_study)
                    for profile in build_profile_rows(case_study_id=args.case_study)
                },
            }
            print(json.dumps(payload, indent=2))
            return
        _print_sources_table(case_study_id=args.case_study)
        return

    if args.command == "analyze":
        analysis = analyze_score(
            Path(args.input),
            segmentation=args.segmentation,
            corpus_profile=args.corpus_profile,
            case_study_id=args.case_study,
        )
        report_path = save_analysis(analysis, Path(args.output_dir))
        plot_tonal_timeline(analysis, Path(args.figures_dir) / f"{analysis.piece_id}_tonal_timeline.png")
        plot_harmonic_activity(analysis, Path(args.figures_dir) / f"{analysis.piece_id}_harmonic_activity.png")
        print(f"Saved analysis to {report_path}")
        print(analysis.summaries["overview"])
        return

    if args.command == "analyze-corpus":
        input_dir = resolve_symbolic_input_dir(
            args.corpus_profile,
            _path_or_none(args.input_dir),
            case_study_id=args.case_study,
        )
        analyses = analyze_and_save_corpus(
            input_dir,
            Path(args.output_dir),
            segmentation=args.segmentation,
            corpus_profile=args.corpus_profile,
            case_study_id=args.case_study,
        )
        if not analyses:
            print(f"No score files found in {input_dir}")
            return
        print(f"Analyzed {len(analyses)} score(s). Reports written to {args.output_dir}")
        return

    if args.command == "compare":
        input_dir = resolve_symbolic_input_dir(
            args.corpus_profile,
            _path_or_none(args.input_dir),
            case_study_id=args.case_study,
        )
        analyses = analyze_corpus(
            input_dir,
            segmentation=args.segmentation,
            corpus_profile=args.corpus_profile,
            case_study_id=args.case_study,
        )
        if not analyses:
            print(f"No score files found in {input_dir}")
            return
        comparison = compare_analyses(analyses)
        json_path, csv_path = save_comparison(comparison, Path(args.output_dir))
        plot_similarity_heatmap(comparison, Path(args.figures_dir) / "piece_similarity.png")
        print(f"Saved comparison JSON to {json_path}")
        print(f"Saved comparison CSV to {csv_path}")
        return

    if args.command == "analyze-audio":
        try:
            analysis = analyze_audio(
                Path(args.input),
                backend=args.backend,
                corpus_profile=args.audio_profile,
                case_study_id=args.case_study,
            )
        except (RuntimeError, ValueError) as exc:
            print(str(exc))
            return
        report_path = save_audio_analysis(analysis, Path(args.output_dir))
        print(f"Saved audio analysis to {report_path}")
        print(analysis.summaries["overview"])
        return

    if args.command == "analyze-audio-corpus":
        try:
            input_dir = resolve_audio_input_dir(
                args.audio_profile,
                _path_or_none(args.input_dir),
                case_study_id=args.case_study,
            )
            analyses = analyze_and_save_audio_corpus(
                input_dir,
                Path(args.output_dir),
                backend=args.backend,
                corpus_profile=args.audio_profile,
                case_study_id=args.case_study,
            )
        except (RuntimeError, ValueError) as exc:
            print(str(exc))
            return
        if not analyses:
            print(f"No audio files found in {input_dir}")
            return
        print(f"Analyzed {len(analyses)} audio file(s). Reports written to {args.output_dir}")
        return

    if args.command == "compare-audio":
        try:
            input_dir = resolve_audio_input_dir(
                args.audio_profile,
                _path_or_none(args.input_dir),
                case_study_id=args.case_study,
            )
            analyses = analyze_audio_corpus(
                input_dir,
                backend=args.backend,
                corpus_profile=args.audio_profile,
                case_study_id=args.case_study,
            )
        except (RuntimeError, ValueError) as exc:
            print(str(exc))
            return
        if not analyses:
            print(f"No audio files found in {input_dir}")
            return
        comparison = compare_audio_analyses(analyses)
        json_path, csv_path = save_audio_comparison(comparison, Path(args.output_dir))
        print(f"Saved audio comparison JSON to {json_path}")
        print(f"Saved audio comparison CSV to {csv_path}")
        return

    if args.command == "validate-score-audio":
        validation = validate_score_against_audio(
            Path(args.score),
            Path(args.audio),
            case_study_id=args.case_study,
            audio_profile=args.audio_profile,
            backend=args.backend,
        )
        print(json.dumps(validation.to_dict(), indent=2))
        return

    if args.command == "validate-case-study":
        validations = validate_case_study_pairs(
            case_study_id=args.case_study,
            symbolic_profile=args.symbolic_profile,
            audio_profile=args.audio_profile,
            backend=args.backend,
            symbolic_input_dir=_path_or_none(args.symbolic_input_dir),
            audio_input_dir=_path_or_none(args.audio_input_dir),
        )
        if not validations:
            print("No matching score/audio pairs were found.")
            return
        json_path, csv_path = save_validations(validations, Path(args.output_dir))
        print(f"Saved validation JSON to {json_path}")
        print(f"Saved validation CSV to {csv_path}")
        return

    parser.print_help()
