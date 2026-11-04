from pathlib import Path

from bach_preludes_analysis.comparison import compare_analyses
from bach_preludes_analysis.models import PieceAnalysis


def test_compare_analyses_returns_similarity_matrix():
    left = PieceAnalysis(
        piece_id="piece_a",
        source_path=Path("a.musicxml"),
        measure_count=16,
        global_key="C major",
        harmonic_rhythm={"changes_per_measure": 2.0, "average_segment_duration_ql": 1.0},
        chromaticism={"chromatic_density": 0.1, "dissonance_density": 0.2, "altered_harmony_count": 1},
        voice_leading={"parallel_perfects": 0, "contrary_motion_rate": 0.4},
    )
    right = PieceAnalysis(
        piece_id="piece_b",
        source_path=Path("b.musicxml"),
        measure_count=20,
        global_key="G major",
        harmonic_rhythm={"changes_per_measure": 3.0, "average_segment_duration_ql": 0.5},
        chromaticism={"chromatic_density": 0.2, "dissonance_density": 0.3, "altered_harmony_count": 2},
        voice_leading={"parallel_perfects": 1, "contrary_motion_rate": 0.5},
    )

    comparison = compare_analyses([left, right])

    assert len(comparison.feature_rows) == 2
    assert set(comparison.similarity_matrix) == {"piece_a", "piece_b"}
    assert comparison.similarity_matrix["piece_a"]["piece_a"] == 1.0
