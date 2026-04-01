from __future__ import annotations

from itertools import combinations

from music21 import key, note, stream

from bach_preludes_analysis.models import HarmonicSegment


def _scale_pitch_classes(key_label: str) -> set[int]:
    tonic, mode = key_label.split(" ", maxsplit=1)
    local_key = key.Key(tonic, mode)
    return {pitch_obj.pitchClass for pitch_obj in local_key.getScale().pitches[:7]}


def analyze_chromaticism(
    score: stream.Score,
    segments: list[HarmonicSegment],
    global_key_label: str,
) -> dict[str, float | int]:
    scale_pitch_classes = _scale_pitch_classes(global_key_label)
    score_notes = [element for element in score.flatten().notes if isinstance(element, note.Note)]
    total_notes = len(score_notes)
    chromatic_notes = sum(1 for element in score_notes if element.pitch.pitchClass not in scale_pitch_classes)

    total_intervals = 0
    dissonant_intervals = 0
    dissonant_classes = {1, 2, 6, 10, 11}
    for segment in segments:
        for first_pitch_class, second_pitch_class in combinations(segment.pitch_classes, 2):
            interval_class = abs(first_pitch_class - second_pitch_class) % 12
            total_intervals += 1
            if interval_class in dissonant_classes:
                dissonant_intervals += 1

    altered_harmony_count = 0
    for segment in segments:
        roman_label = segment.roman_numeral or ""
        if any(symbol in roman_label for symbol in ("#", "-", "b", "+", "o", "/")):
            altered_harmony_count += 1

    return {
        "total_notes": total_notes,
        "chromatic_notes": chromatic_notes,
        "chromatic_density": round(chromatic_notes / max(1, total_notes), 4),
        "altered_harmony_count": altered_harmony_count,
        "dissonant_intervals": dissonant_intervals,
        "dissonance_density": round(dissonant_intervals / max(1, total_intervals), 4),
    }
