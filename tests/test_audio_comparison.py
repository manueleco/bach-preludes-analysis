from pathlib import Path

from bach_preludes_analysis.comparison import compare_audio_analyses
from bach_preludes_analysis.models import AudioAnalysis


def test_compare_audio_analyses_returns_similarity_matrix():
    left = AudioAnalysis(
        prelude_id="prelude_audio_a",
        source_path=Path("a.wav"),
        backend="essentia",
        duration_seconds=90.0,
        sample_rate=44100,
        tempo_bpm=84.0,
        beat_count=120,
        beat_confidence=0.7,
        key_strength=0.8,
        metering={"rms_mean": 0.1, "rms_std": 0.02, "peak_dbfs": -1.0, "crest_factor": 1.5},
        spectral={"spectral_centroid_mean": 1200.0, "spectral_centroid_std": 140.0, "spectral_flux_mean": 0.02, "spectral_flux_std": 0.01},
    )
    right = AudioAnalysis(
        prelude_id="prelude_audio_b",
        source_path=Path("b.wav"),
        backend="essentia",
        duration_seconds=95.0,
        sample_rate=44100,
        tempo_bpm=78.0,
        beat_count=110,
        beat_confidence=0.6,
        key_strength=0.75,
        metering={"rms_mean": 0.12, "rms_std": 0.03, "peak_dbfs": -0.8, "crest_factor": 1.7},
        spectral={"spectral_centroid_mean": 1100.0, "spectral_centroid_std": 130.0, "spectral_flux_mean": 0.03, "spectral_flux_std": 0.012},
    )

    comparison = compare_audio_analyses([left, right])

    assert len(comparison.feature_rows) == 2
    assert set(comparison.similarity_matrix) == {"prelude_audio_a", "prelude_audio_b"}
    assert comparison.similarity_matrix["prelude_audio_a"]["prelude_audio_a"] == 1.0
