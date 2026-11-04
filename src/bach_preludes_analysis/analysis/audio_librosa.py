from __future__ import annotations

from pathlib import Path

import numpy as np

from bach_preludes_analysis.analysis.audio_metrics import amplitude_to_db, summarize_expression
from bach_preludes_analysis.config import DEFAULT_CASE_STUDY_ID
from bach_preludes_analysis.io import infer_piece_id
from bach_preludes_analysis.models import AudioAnalysis

PITCH_CLASS_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
KRUMHANSL_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KRUMHANSL_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def _load_librosa():
    try:
        import librosa  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "No compatible audio backend is installed. "
            "Install the project's audio extra or add Essentia manually."
        ) from exc
    return librosa


def _safe_correlation(left: np.ndarray, right: np.ndarray) -> float:
    if np.allclose(left.std(), 0.0) or np.allclose(right.std(), 0.0):
        return 0.0
    return float(np.corrcoef(left, right)[0, 1])


def _estimate_key_from_chroma(chroma_vector: np.ndarray) -> tuple[str, str, float]:
    major_scores = [_safe_correlation(chroma_vector, np.roll(KRUMHANSL_MAJOR, shift)) for shift in range(12)]
    minor_scores = [_safe_correlation(chroma_vector, np.roll(KRUMHANSL_MINOR, shift)) for shift in range(12)]

    best_major = int(np.argmax(major_scores))
    best_minor = int(np.argmax(minor_scores))
    major_value = major_scores[best_major]
    minor_value = minor_scores[best_minor]

    if major_value >= minor_value:
        return PITCH_CLASS_NAMES[best_major], "major", round(float(major_value), 4)
    return PITCH_CLASS_NAMES[best_minor], "minor", round(float(minor_value), 4)


def analyze_audio_with_librosa(
    input_path: Path,
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
    sample_rate: int = 44100,
    frame_size: int = 4096,
    hop_size: int = 2048,
) -> AudioAnalysis:
    librosa = _load_librosa()

    audio, detected_sample_rate = librosa.load(str(input_path), sr=sample_rate, mono=True)
    if len(audio) == 0:
        raise ValueError(f"Audio file is empty or unreadable: {input_path}")

    duration_seconds = float(librosa.get_duration(y=audio, sr=detected_sample_rate))
    onset_envelope = librosa.onset.onset_strength(y=audio, sr=detected_sample_rate, hop_length=hop_size)
    tempo, beat_frames = librosa.beat.beat_track(y=audio, sr=detected_sample_rate, hop_length=hop_size)
    beat_times = librosa.frames_to_time(beat_frames, sr=detected_sample_rate, hop_length=hop_size)
    rms = librosa.feature.rms(y=audio, frame_length=frame_size, hop_length=hop_size)[0]
    spectral_centroid = librosa.feature.spectral_centroid(
        y=audio,
        sr=detected_sample_rate,
        n_fft=frame_size,
        hop_length=hop_size,
    )[0]
    spectral_bandwidth = librosa.feature.spectral_bandwidth(
        y=audio,
        sr=detected_sample_rate,
        n_fft=frame_size,
        hop_length=hop_size,
    )[0]
    spectral_flatness = librosa.feature.spectral_flatness(
        y=audio,
        n_fft=frame_size,
        hop_length=hop_size,
    )[0]
    chroma = librosa.feature.chroma_stft(
        y=audio,
        sr=detected_sample_rate,
        n_fft=frame_size,
        hop_length=hop_size,
    )
    chroma_mean = np.mean(chroma, axis=1)
    key, scale, key_strength = _estimate_key_from_chroma(chroma_mean)

    absolute_peak = float(np.max(np.abs(audio)))
    global_rms = float(np.sqrt(np.mean(np.square(audio))))
    crest_factor = absolute_peak / max(global_rms, 1e-12)
    peak_dbfs = amplitude_to_db(absolute_peak)
    rms_mean = float(np.mean(rms))
    rms_std = float(np.std(rms))
    level_dbfs_mean = amplitude_to_db(rms_mean)
    expression = summarize_expression(
        rms_values=rms,
        activation_values=onset_envelope,
        beat_times=np.asarray(beat_times, dtype=float),
        duration_seconds=duration_seconds,
        frame_hop_seconds=float(hop_size) / float(detected_sample_rate),
    )

    return AudioAnalysis(
        piece_id=infer_piece_id(input_path, case_study_id=case_study_id),
        source_path=input_path,
        backend="librosa",
        duration_seconds=round(duration_seconds, 3),
        sample_rate=int(detected_sample_rate),
        tempo_bpm=round(float(np.atleast_1d(tempo)[0]), 3),
        beat_count=len(beat_frames),
        beat_confidence=None,
        estimated_key=key,
        estimated_scale=scale,
        key_strength=key_strength,
        metering={
            "level_dbfs_mean": round(level_dbfs_mean, 4),
            "rms_mean": round(rms_mean, 6),
            "rms_std": round(rms_std, 6),
            "peak_dbfs": round(peak_dbfs, 4),
            "crest_factor": round(crest_factor, 4),
        },
        spectral={
            "spectral_centroid_mean": round(float(np.mean(spectral_centroid)), 4),
            "spectral_centroid_std": round(float(np.std(spectral_centroid)), 4),
            "spectral_bandwidth_mean": round(float(np.mean(spectral_bandwidth)), 4),
            "spectral_bandwidth_std": round(float(np.std(spectral_bandwidth)), 4),
            "spectral_flatness_mean": round(float(np.mean(spectral_flatness)), 6),
            "spectral_flatness_std": round(float(np.std(spectral_flatness)), 6),
            "spectral_flux_mean": round(float(np.mean(onset_envelope)), 6),
            "spectral_flux_std": round(float(np.std(onset_envelope)), 6),
        },
        tonal={
            "estimated_key": key,
            "estimated_scale": scale,
            "key_strength": key_strength,
            "chroma_profile": [round(float(value), 6) for value in chroma_mean.tolist()],
        },
        expression={
            name: round(float(value), 6) if isinstance(value, float) and value is not None else value
            for name, value in expression.items()
        },
    )
