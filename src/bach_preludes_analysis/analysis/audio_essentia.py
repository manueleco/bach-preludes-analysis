from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np

from bach_preludes_analysis.io import infer_prelude_id
from bach_preludes_analysis.models import AudioAnalysis


def _load_essentia_standard():
    try:
        import essentia.standard as es  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Essentia is not installed in this environment. "
            "Install it first, or use the librosa fallback backend."
        ) from exc
    return es


def _framewise_features(
    es: Any,
    audio: np.ndarray,
    sample_rate: int,
    frame_size: int,
    hop_size: int,
) -> dict[str, float]:
    window = es.Windowing(type="hann")
    spectrum = es.Spectrum()
    rms_algorithm = es.RMS()
    centroid_algorithm = es.Centroid(range=float(sample_rate) / 2.0)
    flux_algorithm = es.Flux()

    rms_values: list[float] = []
    centroid_values: list[float] = []
    flux_values: list[float] = []
    previous_spectrum = None

    for frame in es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size, startFromZero=True):
        if len(frame) == 0:
            continue
        windowed = window(frame)
        current_spectrum = spectrum(windowed)
        rms_values.append(float(rms_algorithm(frame)))
        centroid_values.append(float(centroid_algorithm(current_spectrum)))
        if previous_spectrum is not None:
            flux_values.append(float(flux_algorithm(current_spectrum, previous_spectrum)))
        previous_spectrum = current_spectrum

    return {
        "rms_mean": float(np.mean(rms_values)) if rms_values else 0.0,
        "rms_std": float(np.std(rms_values)) if rms_values else 0.0,
        "spectral_centroid_mean": float(np.mean(centroid_values)) if centroid_values else 0.0,
        "spectral_centroid_std": float(np.std(centroid_values)) if centroid_values else 0.0,
        "spectral_flux_mean": float(np.mean(flux_values)) if flux_values else 0.0,
        "spectral_flux_std": float(np.std(flux_values)) if flux_values else 0.0,
    }


def analyze_audio_with_essentia(
    input_path: Path,
    sample_rate: int = 44100,
    frame_size: int = 4096,
    hop_size: int = 2048,
) -> AudioAnalysis:
    es = _load_essentia_standard()

    audio = es.MonoLoader(filename=str(input_path), sampleRate=sample_rate)()
    if len(audio) == 0:
        raise ValueError(f"Audio file is empty or unreadable: {input_path}")

    duration_seconds = float(len(audio) / sample_rate)
    bpm, beats, beats_confidence, _, _ = es.RhythmExtractor2013(method="multifeature")(audio)
    key, scale, strength = es.KeyExtractor(sampleRate=sample_rate)(audio)

    frame_stats = _framewise_features(es, audio, sample_rate, frame_size, hop_size)
    absolute_peak = float(np.max(np.abs(audio)))
    global_rms = float(np.sqrt(np.mean(np.square(audio))))
    crest_factor = absolute_peak / max(global_rms, 1e-12)
    peak_dbfs = 20.0 * math.log10(max(absolute_peak, 1e-12))
    loudness = float(es.Loudness()(audio))

    analysis = AudioAnalysis(
        prelude_id=infer_prelude_id(input_path),
        source_path=input_path,
        backend="essentia",
        duration_seconds=round(duration_seconds, 3),
        sample_rate=sample_rate,
        tempo_bpm=round(float(bpm), 3),
        beat_count=len(beats),
        beat_confidence=round(float(beats_confidence), 4),
        estimated_key=str(key),
        estimated_scale=str(scale),
        key_strength=round(float(strength), 4),
        metering={
            "integrated_loudness": round(loudness, 4),
            "rms_mean": round(frame_stats["rms_mean"], 6),
            "rms_std": round(frame_stats["rms_std"], 6),
            "peak_dbfs": round(peak_dbfs, 4),
            "crest_factor": round(crest_factor, 4),
        },
        spectral={
            "spectral_centroid_mean": round(frame_stats["spectral_centroid_mean"], 4),
            "spectral_centroid_std": round(frame_stats["spectral_centroid_std"], 4),
            "spectral_flux_mean": round(frame_stats["spectral_flux_mean"], 6),
            "spectral_flux_std": round(frame_stats["spectral_flux_std"], 6),
        },
        tonal={
            "estimated_key": str(key),
            "estimated_scale": str(scale),
            "key_strength": round(float(strength), 4),
        },
    )
    return analysis
