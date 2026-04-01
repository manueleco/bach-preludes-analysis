from __future__ import annotations

import argparse
from pathlib import Path

from bach_preludes_analysis.audio_pipeline import (
    analyze_and_save_audio_corpus,
    analyze_audio,
    analyze_audio_corpus,
    save_audio_analysis,
    save_audio_comparison,
)
from bach_preludes_analysis.config import OUTPUT_FIGURES_DIR, OUTPUT_REPORTS_DIR
from bach_preludes_analysis.comparison import compare_analyses, compare_audio_analyses
from bach_preludes_analysis.pipeline import analyze_and_save_corpus, analyze_corpus, analyze_score, save_analysis, save_comparison
from bach_preludes_analysis.reporting.visuals import plot_harmonic_activity, plot_similarity_heatmap, plot_tonal_timeline


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze and compare Bach preludes from symbolic scores and optional audio.")
    subparsers = parser.add_subparsers(dest="command")

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a single score file.")
    analyze_parser.add_argument("--input", required=True, help="Path to a MusicXML, MXL, XML, MIDI, or MID file.")
    analyze_parser.add_argument("--segmentation", choices=["beat", "event"], default="beat")
    analyze_parser.add_argument("--output-dir", default=str(OUTPUT_REPORTS_DIR))
    analyze_parser.add_argument("--figures-dir", default=str(OUTPUT_FIGURES_DIR))

    corpus_parser = subparsers.add_parser("analyze-corpus", help="Analyze all score files in a folder.")
    corpus_parser.add_argument("--input-dir", required=True, help="Directory with raw score files.")
    corpus_parser.add_argument("--segmentation", choices=["beat", "event"], default="beat")
    corpus_parser.add_argument("--output-dir", default=str(OUTPUT_REPORTS_DIR))

    compare_parser = subparsers.add_parser("compare", help="Compare all score files in a folder.")
    compare_parser.add_argument("--input-dir", required=True, help="Directory with raw score files.")
    compare_parser.add_argument("--segmentation", choices=["beat", "event"], default="beat")
    compare_parser.add_argument("--output-dir", default=str(OUTPUT_REPORTS_DIR))
    compare_parser.add_argument("--figures-dir", default=str(OUTPUT_FIGURES_DIR))

    analyze_audio_parser = subparsers.add_parser("analyze-audio", help="Analyze a single audio file with Essentia.")
    analyze_audio_parser.add_argument("--input", required=True, help="Path to an audio file such as WAV, FLAC, MP3, or AIFF.")
    analyze_audio_parser.add_argument("--backend", choices=["auto", "essentia", "librosa"], default="auto")
    analyze_audio_parser.add_argument("--output-dir", default=str(OUTPUT_REPORTS_DIR / "audio"))

    corpus_audio_parser = subparsers.add_parser("analyze-audio-corpus", help="Analyze all audio files in a folder.")
    corpus_audio_parser.add_argument("--input-dir", required=True, help="Directory with raw audio files.")
    corpus_audio_parser.add_argument("--backend", choices=["auto", "essentia", "librosa"], default="auto")
    corpus_audio_parser.add_argument("--output-dir", default=str(OUTPUT_REPORTS_DIR / "audio"))

    compare_audio_parser = subparsers.add_parser("compare-audio", help="Compare all audio files in a folder.")
    compare_audio_parser.add_argument("--input-dir", required=True, help="Directory with raw audio files.")
    compare_audio_parser.add_argument("--backend", choices=["auto", "essentia", "librosa"], default="auto")
    compare_audio_parser.add_argument("--output-dir", default=str(OUTPUT_REPORTS_DIR / "audio"))
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        analysis = analyze_score(Path(args.input), segmentation=args.segmentation)
        report_path = save_analysis(analysis, Path(args.output_dir))
        plot_tonal_timeline(analysis, Path(args.figures_dir) / f"{analysis.prelude_id}_tonal_timeline.png")
        plot_harmonic_activity(analysis, Path(args.figures_dir) / f"{analysis.prelude_id}_harmonic_activity.png")
        print(f"Saved analysis to {report_path}")
        print(analysis.summaries["overview"])
        return

    if args.command == "analyze-corpus":
        analyses = analyze_and_save_corpus(Path(args.input_dir), Path(args.output_dir), segmentation=args.segmentation)
        if not analyses:
            print(f"No score files found in {args.input_dir}")
            return
        print(f"Analyzed {len(analyses)} score(s). Reports written to {args.output_dir}")
        return

    if args.command == "compare":
        analyses = analyze_corpus(Path(args.input_dir), segmentation=args.segmentation)
        if not analyses:
            print(f"No score files found in {args.input_dir}")
            return
        comparison = compare_analyses(analyses)
        json_path, csv_path = save_comparison(comparison, Path(args.output_dir))
        plot_similarity_heatmap(comparison, Path(args.figures_dir) / "prelude_similarity.png")
        print(f"Saved comparison JSON to {json_path}")
        print(f"Saved comparison CSV to {csv_path}")
        return

    if args.command == "analyze-audio":
        try:
            analysis = analyze_audio(Path(args.input), backend=args.backend)
        except (RuntimeError, ValueError) as exc:
            print(str(exc))
            return
        report_path = save_audio_analysis(analysis, Path(args.output_dir))
        print(f"Saved audio analysis to {report_path}")
        print(analysis.summaries["overview"])
        return

    if args.command == "analyze-audio-corpus":
        try:
            analyses = analyze_and_save_audio_corpus(Path(args.input_dir), Path(args.output_dir), backend=args.backend)
        except (RuntimeError, ValueError) as exc:
            print(str(exc))
            return
        if not analyses:
            print(f"No audio files found in {args.input_dir}")
            return
        print(f"Analyzed {len(analyses)} audio file(s). Reports written to {args.output_dir}")
        return

    if args.command == "compare-audio":
        try:
            analyses = analyze_audio_corpus(Path(args.input_dir), backend=args.backend)
        except (RuntimeError, ValueError) as exc:
            print(str(exc))
            return
        if not analyses:
            print(f"No audio files found in {args.input_dir}")
            return
        comparison = compare_audio_analyses(analyses)
        json_path, csv_path = save_audio_comparison(comparison, Path(args.output_dir))
        print(f"Saved audio comparison JSON to {json_path}")
        print(f"Saved audio comparison CSV to {csv_path}")
        return

    parser.print_help()
