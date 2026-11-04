from bach_preludes_analysis.analysis.chords import _group_key


class _DummyNote:
    measureNumber = 3
    beat = float("nan")
    offset = 1.5


def test_group_key_tolerates_nan_beats():
    assert _group_key(_DummyNote(), "beat") == (3, None, 1.5)
