from __future__ import annotations

import math

import numpy as np


def amplitude_to_db(amplitude: float) -> float:
    return 20.0 * math.log10(max(float(amplitude), 1e-12))


def summarize_beats(beat_times: np.ndarray) -> dict[str, float | None]:
    if len(beat_times) < 2:
        return {
            "local_tempo_mean_bpm": None,
            "local_tempo_std_bpm": None,
            "rubato_index": None,
            "tempo_range_bpm": None,
        }

    beat_intervals = np.diff(beat_times)
    beat_intervals = beat_intervals[beat_intervals > 1e-9]
    if len(beat_intervals) == 0:
        return {
            "local_tempo_mean_bpm": None,
            "local_tempo_std_bpm": None,
            "rubato_index": None,
            "tempo_range_bpm": None,
        }

    local_tempi = 60.0 / beat_intervals
    return {
        "local_tempo_mean_bpm": float(np.mean(local_tempi)),
        "local_tempo_std_bpm": float(np.std(local_tempi)),
        "rubato_index": float(np.std(beat_intervals) / max(np.mean(beat_intervals), 1e-9)),
        "tempo_range_bpm": float(np.max(local_tempi) - np.min(local_tempi)),
    }


def detect_transient_times(activation_values: np.ndarray, frame_hop_seconds: float) -> np.ndarray:
    if len(activation_values) < 3:
        return np.array([], dtype=float)

    threshold = float(np.mean(activation_values) + np.std(activation_values))
    peak_indices = [
        index
        for index in range(1, len(activation_values) - 1)
        if activation_values[index] > threshold
        and activation_values[index] >= activation_values[index - 1]
        and activation_values[index] >= activation_values[index + 1]
    ]
    if not peak_indices:
        return np.array([], dtype=float)
    return np.asarray(peak_indices, dtype=float) * frame_hop_seconds


def summarize_expression(
    rms_values: np.ndarray,
    activation_values: np.ndarray,
    beat_times: np.ndarray,
    duration_seconds: float,
    frame_hop_seconds: float,
) -> dict[str, float | None]:
    beat_summary = summarize_beats(beat_times)
    if len(rms_values) == 0:
        rms_values = np.array([0.0], dtype=float)

    rms_db = 20.0 * np.log10(np.clip(rms_values, 1e-12, None))
    dynamic_range_db = float(np.percentile(rms_db, 95) - np.percentile(rms_db, 10))
    dynamic_variability_db = float(np.std(rms_db))

    transient_times = detect_transient_times(activation_values, frame_hop_seconds)
    transient_gaps = np.diff(transient_times) if len(transient_times) >= 2 else np.array([], dtype=float)

    articulation = {
        "dynamic_range_db": dynamic_range_db,
        "dynamic_variability_db": dynamic_variability_db,
        "transient_count": int(len(transient_times)),
        "transient_density_per_second": float(len(transient_times) / max(duration_seconds, 1e-9)),
        "median_inter_transient_seconds": (
            float(np.median(transient_gaps)) if len(transient_gaps) else None
        ),
    }
    return {**beat_summary, **articulation}
