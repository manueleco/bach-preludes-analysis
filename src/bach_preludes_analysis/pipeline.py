from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from bach_preludes_analysis.analysis.cadences import detect_cadences
from bach_preludes_analysis.analysis.chords import (
    detect_secondary_functions,
    estimate_harmonic_rhythm,
    extract_harmonic_segments,
)
from bach_preludes_analysis.analysis.chromaticism import analyze_chromaticism
from bach_preludes_analysis.analysis.keys import analyze_global_key, analyze_key_regions
from bach_preludes_analysis.analysis.non_chord_tones import detect_non_chord_tones
from bach_preludes_analysis.analysis.sequences import detect_recurrent_progressions
from bach_preludes_analysis.analysis.voice_leading import analyze_voice_leading
from bach_preludes_analysis.comparison import build_feature_table, compare_analyses
from bach_preludes_analysis.io import discover_score_paths, ensure_directory, infer_prelude_id, load_score
from bach_preludes_analysis.models import ComparisonResult, PreludeAnalysis
from bach_preludes_analysis.reporting.explainers import build_musician_summary


def _measure_count(score) -> int:
    measures = []
    for part in score.parts if score.parts else [score]:
        measures.extend(measure.measureNumber for measure in part.getElementsByClass("Measure"))
    return max((number for number in measures if number is not None), default=0)


def _key_label(key_obj) -> str:
    return f"{key_obj.tonicPitchNameWithCase} {key_obj.mode}"


def analyze_score(input_path: Path, segmentation: str = "beat") -> PreludeAnalysis:
    score = load_score(input_path)
    global_key = analyze_global_key(score)
    global_key_label = _key_label(global_key)
    key_regions = analyze_key_regions(score)
    segments, texture_profile = extract_harmonic_segments(score, key_regions, global_key_label, granularity=segmentation)
    harmonic_rhythm = estimate_harmonic_rhythm(segments)
    secondary_functions = detect_secondary_functions(segments)
    cadences = detect_cadences(segments)
    non_chord_tones = detect_non_chord_tones(score, segments)
    sequences = detect_recurrent_progressions(segments)
    chromaticism = analyze_chromaticism(score, segments, global_key_label)
    voice_leading, voice_leading_events = analyze_voice_leading(segments)

    analysis = PreludeAnalysis(
        prelude_id=infer_prelude_id(input_path),
        source_path=input_path,
        measure_count=_measure_count(score),
        global_key=global_key_label,
        key_regions=key_regions,
        segments=segments,
        harmonic_rhythm=harmonic_rhythm,
        cadences=cadences,
        secondary_functions=secondary_functions,
        non_chord_tones=non_chord_tones,
        sequences=sequences,
        chromaticism=chromaticism,
        texture_profile=texture_profile,
        voice_leading=voice_leading,
        voice_leading_events=voice_leading_events,
    )
    analysis.summaries = build_musician_summary(analysis)
    return analysis


def analyze_corpus(input_dir: Path, segmentation: str = "beat") -> list[PreludeAnalysis]:
    analyses = []
    for input_path in discover_score_paths(input_dir):
        analyses.append(analyze_score(input_path, segmentation=segmentation))
    return analyses


def save_analysis(analysis: PreludeAnalysis, output_dir: Path) -> Path:
    ensure_directory(output_dir)
    output_path = output_dir / f"{analysis.prelude_id}_analysis.json"
    output_path.write_text(json.dumps(analysis.to_dict(), indent=2), encoding="utf-8")
    return output_path


def save_comparison(comparison: ComparisonResult, output_dir: Path) -> tuple[Path, Path]:
    ensure_directory(output_dir)
    json_path = output_dir / "comparison_summary.json"
    csv_path = output_dir / "comparison_features.csv"

    json_path.write_text(json.dumps(comparison.to_dict(), indent=2), encoding="utf-8")
    pd.DataFrame(comparison.feature_rows).to_csv(csv_path, index=False)
    return json_path, csv_path


def analyze_and_save_corpus(input_dir: Path, output_dir: Path, segmentation: str = "beat") -> list[PreludeAnalysis]:
    analyses = analyze_corpus(input_dir, segmentation=segmentation)
    for analysis in analyses:
        save_analysis(analysis, output_dir)
    return analyses


def compare_corpus(input_dir: Path, output_dir: Path, segmentation: str = "beat") -> ComparisonResult:
    analyses = analyze_corpus(input_dir, segmentation=segmentation)
    comparison = compare_analyses(analyses)
    save_comparison(comparison, output_dir)
    return comparison
