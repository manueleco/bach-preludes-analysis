from pathlib import Path

from music21 import meter, note, stream

from bach_preludes_analysis.pipeline import analyze_score


def test_monodic_arpeggio_uses_implicit_harmony_window(tmp_path):
    score = stream.Score()
    part = stream.Part()
    part.append(meter.TimeSignature("4/4"))

    for pitches in [("G3", "B3", "D4", "G4"), ("A3", "C4", "E4", "A4")]:
        measure = stream.Measure()
        for pitch_name in pitches:
            current_note = note.Note(pitch_name)
            current_note.quarterLength = 1
            measure.append(current_note)
        part.append(measure)

    score.append(part)
    output_path = tmp_path / "suite_01_prelude_g_major_bwv1007.musicxml"
    score.write("musicxml", fp=str(output_path))

    analysis = analyze_score(output_path)

    assert analysis.texture_profile["is_implied_harmony"] is True
    assert analysis.segments[0].inference_strategy == "implicit_harmony_window"
    assert analysis.segments[0].roman_numeral in {"I", "i"}
