from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from bach_preludes_analysis.analysis.audio_essentia import analyze_audio_with_essentia
from bach_preludes_analysis.analysis.audio_librosa import analyze_audio_with_librosa
from bach_preludes_analysis.case_studies import get_case_study
from bach_preludes_analysis.comparison import compare_audio_analyses
from bach_preludes_analysis.config import DEFAULT_CASE_STUDY_ID
from bach_preludes_analysis.corpus_profiles import get_profile, resolve_audio_input_dir
from bach_preludes_analysis.io import discover_audio_paths, ensure_directory
from bach_preludes_analysis.models import AudioAnalysis, ComparisonResult
from bach_preludes_analysis.reporting.audio_explainers import build_audio_summary


def analyze_audio(
    input_path: Path,
    backend: str = "auto",
    corpus_profile: str = "single_interpreter_reference",
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
) -> AudioAnalysis:
    selected_backend = backend.lower()
    analysis: AudioAnalysis | None = None
    last_error: Exception | None = None
    case_study = get_case_study(case_study_id)
    profile = get_profile(corpus_profile, case_study_id=case_study_id)
    if profile.domain != "audio":
        raise ValueError(f"Profile '{corpus_profile}' is not an audio corpus profile.")

    if selected_backend in {"auto", "essentia"}:
        try:
            analysis = analyze_audio_with_essentia(input_path, case_study_id=case_study_id)
        except (RuntimeError, ValueError) as exc:
            last_error = exc
            if selected_backend == "essentia":
                raise

    if analysis is None and selected_backend in {"auto", "librosa"}:
        try:
            analysis = analyze_audio_with_librosa(input_path, case_study_id=case_study_id)
        except (RuntimeError, ValueError) as exc:
            last_error = exc
            if selected_backend == "librosa":
                raise

    if analysis is None:
        if last_error is not None:
            raise RuntimeError(str(last_error))
        raise RuntimeError(f"Unsupported audio backend: {backend}")

    analysis.case_study_id = case_study.case_study_id
    analysis.case_study_label = case_study.label
    analysis.corpus_profile_id = profile.profile_id
    analysis.corpus_profile_label = profile.label
    analysis.reliability = dict(profile.reliability)
    analysis.source_context = {
        "description": profile.description,
        "role": profile.role,
        "source_family": profile.source_family,
        "reference_url": profile.reference_url,
        "case_study": case_study.label,
        "composer": case_study.composer,
        "collection_title": case_study.collection_title,
    }
    analysis.summaries = build_audio_summary(analysis)
    return analysis


def analyze_audio_corpus(
    input_dir: Path | None = None,
    backend: str = "auto",
    corpus_profile: str = "single_interpreter_reference",
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
) -> list[AudioAnalysis]:
    resolved_input_dir = resolve_audio_input_dir(
        corpus_profile,
        explicit_input_dir=input_dir,
        case_study_id=case_study_id,
    )
    analyses = []
    for input_path in discover_audio_paths(resolved_input_dir):
        analyses.append(
            analyze_audio(
                input_path,
                backend=backend,
                corpus_profile=corpus_profile,
                case_study_id=case_study_id,
            )
        )
    return analyses


def save_audio_analysis(analysis: AudioAnalysis, output_dir: Path) -> Path:
    ensure_directory(output_dir)
    output_path = output_dir / f"{analysis.piece_id}_audio_analysis.json"
    output_path.write_text(json.dumps(analysis.to_dict(), indent=2), encoding="utf-8")
    return output_path


def save_audio_comparison(comparison: ComparisonResult, output_dir: Path) -> tuple[Path, Path]:
    ensure_directory(output_dir)
    json_path = output_dir / "audio_comparison_summary.json"
    csv_path = output_dir / "audio_comparison_features.csv"
    json_path.write_text(json.dumps(comparison.to_dict(), indent=2), encoding="utf-8")
    pd.DataFrame(comparison.feature_rows).to_csv(csv_path, index=False)
    return json_path, csv_path


def analyze_and_save_audio_corpus(
    input_dir: Path | None,
    output_dir: Path,
    backend: str = "auto",
    corpus_profile: str = "single_interpreter_reference",
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
) -> list[AudioAnalysis]:
    analyses = analyze_audio_corpus(
        input_dir,
        backend=backend,
        corpus_profile=corpus_profile,
        case_study_id=case_study_id,
    )
    for analysis in analyses:
        save_audio_analysis(analysis, output_dir)
    return analyses


def compare_audio_corpus(
    input_dir: Path | None,
    output_dir: Path,
    backend: str = "auto",
    corpus_profile: str = "single_interpreter_reference",
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
) -> ComparisonResult:
    analyses = analyze_audio_corpus(
        input_dir,
        backend=backend,
        corpus_profile=corpus_profile,
        case_study_id=case_study_id,
    )
    comparison = compare_audio_analyses(analyses)
    save_audio_comparison(comparison, output_dir)
    return comparison
