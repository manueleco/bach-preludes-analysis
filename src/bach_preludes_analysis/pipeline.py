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
from bach_preludes_analysis.case_studies import get_case_study
from bach_preludes_analysis.comparison import compare_analyses
from bach_preludes_analysis.config import DEFAULT_CASE_STUDY_ID
from bach_preludes_analysis.corpus_profiles import get_profile, resolve_symbolic_input_dir
from bach_preludes_analysis.io import discover_score_paths, ensure_directory, infer_piece_id, load_score
from bach_preludes_analysis.models import ComparisonResult, PieceAnalysis
from bach_preludes_analysis.reporting.explainers import build_musician_summary


def _measure_count(score) -> int:
    measures = []
    for part in score.parts if score.parts else [score]:
        measures.extend(measure.measureNumber for measure in part.getElementsByClass("Measure"))
    return max((number for number in measures if number is not None), default=0)


def _key_label(key_obj) -> str:
    return f"{key_obj.tonicPitchNameWithCase} {key_obj.mode}"


def analyze_score(
    input_path: Path,
    segmentation: str = "beat",
    corpus_profile: str = "official_curated",
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
) -> PieceAnalysis:
    case_study = get_case_study(case_study_id)
    profile = get_profile(corpus_profile, case_study_id=case_study_id)
    if profile.domain != "symbolic":
        raise ValueError(f"Profile '{corpus_profile}' is not a symbolic corpus profile.")

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

    analysis = PieceAnalysis(
        piece_id=infer_piece_id(input_path, case_study_id=case_study_id),
        source_path=input_path,
        measure_count=_measure_count(score),
        global_key=global_key_label,
        case_study_id=case_study.case_study_id,
        case_study_label=case_study.label,
        corpus_profile_id=profile.profile_id,
        corpus_profile_label=profile.label,
        reliability=dict(profile.reliability),
        source_context={
            "description": profile.description,
            "role": profile.role,
            "source_family": profile.source_family,
            "reference_url": profile.reference_url,
            "case_study": case_study.label,
            "composer": case_study.composer,
            "collection_title": case_study.collection_title,
        },
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


def analyze_corpus(
    input_dir: Path | None = None,
    segmentation: str = "beat",
    corpus_profile: str = "official_curated",
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
) -> list[PieceAnalysis]:
    resolved_input_dir = resolve_symbolic_input_dir(
        corpus_profile,
        explicit_input_dir=input_dir,
        case_study_id=case_study_id,
    )
    analyses = []
    for input_path in discover_score_paths(resolved_input_dir):
        analyses.append(
            analyze_score(
                input_path,
                segmentation=segmentation,
                corpus_profile=corpus_profile,
                case_study_id=case_study_id,
            )
        )
    return analyses


def save_analysis(analysis: PieceAnalysis, output_dir: Path) -> Path:
    ensure_directory(output_dir)
    output_path = output_dir / f"{analysis.piece_id}_analysis.json"
    output_path.write_text(json.dumps(analysis.to_dict(), indent=2), encoding="utf-8")
    return output_path


def save_comparison(comparison: ComparisonResult, output_dir: Path) -> tuple[Path, Path]:
    ensure_directory(output_dir)
    json_path = output_dir / "comparison_summary.json"
    csv_path = output_dir / "comparison_features.csv"

    json_path.write_text(json.dumps(comparison.to_dict(), indent=2), encoding="utf-8")
    pd.DataFrame(comparison.feature_rows).to_csv(csv_path, index=False)
    return json_path, csv_path


def analyze_and_save_corpus(
    input_dir: Path | None,
    output_dir: Path,
    segmentation: str = "beat",
    corpus_profile: str = "official_curated",
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
) -> list[PieceAnalysis]:
    analyses = analyze_corpus(
        input_dir,
        segmentation=segmentation,
        corpus_profile=corpus_profile,
        case_study_id=case_study_id,
    )
    for analysis in analyses:
        save_analysis(analysis, output_dir)
    return analyses


def compare_corpus(
    input_dir: Path | None,
    output_dir: Path,
    segmentation: str = "beat",
    corpus_profile: str = "official_curated",
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
) -> ComparisonResult:
    analyses = analyze_corpus(
        input_dir,
        segmentation=segmentation,
        corpus_profile=corpus_profile,
        case_study_id=case_study_id,
    )
    comparison = compare_analyses(analyses)
    save_comparison(comparison, output_dir)
    return comparison
