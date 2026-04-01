from __future__ import annotations

import numpy as np
import pandas as pd

from bach_preludes_analysis.models import AudioAnalysis, ComparisonResult, PreludeAnalysis


def _cadence_count(analysis: PreludeAnalysis, cadence_type: str) -> int:
    return sum(1 for cadence in analysis.cadences if cadence.cadence_type == cadence_type)


def build_feature_table(analyses: list[PreludeAnalysis]) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for analysis in analyses:
        rows.append(
            {
                "prelude_id": analysis.prelude_id,
                "global_key": analysis.global_key,
                "measure_count": analysis.measure_count,
                "segment_count": len(analysis.segments),
                "local_key_regions": len(analysis.key_regions),
                "modulation_count": max(0, len(analysis.key_regions) - 1),
                "secondary_functions": len(analysis.secondary_functions),
                "cadences_total": len(analysis.cadences),
                "cadence_pac": _cadence_count(analysis, "PAC"),
                "cadence_iac": _cadence_count(analysis, "IAC"),
                "cadence_half": _cadence_count(analysis, "half"),
                "cadence_deceptive": _cadence_count(analysis, "deceptive"),
                "cadence_plagal": _cadence_count(analysis, "plagal"),
                "non_chord_tones": len(analysis.non_chord_tones),
                "sequence_patterns": len(analysis.sequences),
                "changes_per_measure": float(analysis.harmonic_rhythm.get("changes_per_measure", 0.0)),
                "avg_segment_duration_ql": float(analysis.harmonic_rhythm.get("average_segment_duration_ql", 0.0)),
                "chromatic_density": float(analysis.chromaticism.get("chromatic_density", 0.0)),
                "dissonance_density": float(analysis.chromaticism.get("dissonance_density", 0.0)),
                "altered_harmony_count": int(analysis.chromaticism.get("altered_harmony_count", 0)),
                "avg_observed_pitch_classes": float(analysis.texture_profile.get("average_observed_pitch_classes", 0.0)),
                "sparse_segment_ratio": float(analysis.texture_profile.get("sparse_segment_ratio", 0.0)),
                "parallel_perfects": int(analysis.voice_leading.get("parallel_perfects", 0)),
                "contrary_motion_rate": float(analysis.voice_leading.get("contrary_motion_rate", 0.0)),
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("prelude_id").reset_index(drop=True)


def _cosine_similarity(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1)
    norms[norms == 0] = 1.0
    return (matrix @ matrix.T) / np.outer(norms, norms)


def comparison_from_feature_table(feature_table: pd.DataFrame, id_column: str = "prelude_id") -> ComparisonResult:
    if feature_table.empty:
        return ComparisonResult(feature_rows=[], similarity_matrix={})

    numeric_columns = feature_table.select_dtypes(include=["number"]).columns
    numeric_matrix = feature_table[numeric_columns].fillna(0.0).to_numpy(dtype=float)

    means = numeric_matrix.mean(axis=0)
    stds = numeric_matrix.std(axis=0)
    stds[stds == 0] = 1.0
    standardized = (numeric_matrix - means) / stds

    similarity = _cosine_similarity(standardized)
    np.fill_diagonal(similarity, 1.0)
    labels = feature_table[id_column].tolist()
    similarity_matrix = {
        left_label: {
            right_label: round(float(similarity[left_index, right_index]), 4)
            for right_index, right_label in enumerate(labels)
        }
        for left_index, left_label in enumerate(labels)
    }

    return ComparisonResult(
        feature_rows=feature_table.to_dict(orient="records"),
        similarity_matrix=similarity_matrix,
    )


def compare_analyses(analyses: list[PreludeAnalysis]) -> ComparisonResult:
    feature_table = build_feature_table(analyses)
    return comparison_from_feature_table(feature_table, id_column="prelude_id")


def build_audio_feature_table(analyses: list[AudioAnalysis]) -> pd.DataFrame:
    rows: list[dict[str, float | int | str | None]] = []
    for analysis in analyses:
        rows.append(
            {
                "prelude_id": analysis.prelude_id,
                "backend": analysis.backend,
                "duration_seconds": analysis.duration_seconds,
                "sample_rate": analysis.sample_rate,
                "tempo_bpm": analysis.tempo_bpm,
                "beat_count": analysis.beat_count,
                "beat_confidence": analysis.beat_confidence,
                "key_strength": analysis.key_strength,
                "level_dbfs_mean": analysis.metering.get("level_dbfs_mean"),
                "rms_mean": analysis.metering.get("rms_mean"),
                "rms_std": analysis.metering.get("rms_std"),
                "peak_dbfs": analysis.metering.get("peak_dbfs"),
                "crest_factor": analysis.metering.get("crest_factor"),
                "spectral_centroid_mean": analysis.spectral.get("spectral_centroid_mean"),
                "spectral_centroid_std": analysis.spectral.get("spectral_centroid_std"),
                "spectral_flux_mean": analysis.spectral.get("spectral_flux_mean"),
                "spectral_flux_std": analysis.spectral.get("spectral_flux_std"),
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("prelude_id").reset_index(drop=True)


def compare_audio_analyses(analyses: list[AudioAnalysis]) -> ComparisonResult:
    feature_table = build_audio_feature_table(analyses)
    return comparison_from_feature_table(feature_table, id_column="prelude_id")
