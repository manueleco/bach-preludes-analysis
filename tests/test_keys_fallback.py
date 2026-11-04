from music21 import note, stream

from bach_preludes_analysis.analysis.keys import analyze_key_regions


def test_analyze_key_regions_falls_back_when_excerpt_is_not_key_analyzable():
    score = stream.Score()
    part = stream.Part()
    measure = stream.Measure(number=1)
    measure.append(note.Rest(quarterLength=4))
    part.append(measure)
    score.append(part)

    regions = analyze_key_regions(score)

    assert regions
    assert regions[0].key == "C major"
