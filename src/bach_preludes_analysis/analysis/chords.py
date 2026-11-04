from __future__ import annotations

import math
from collections import OrderedDict
from statistics import mean

from music21 import chord, harmony, key, note, roman, stream

from bach_preludes_analysis.models import HarmonicSegment, KeyRegion


def _element_pitches(element: note.NotRest | chord.Chord) -> list[note.Pitch]:
    if isinstance(element, note.Note):
        return [element.pitch]
    if isinstance(element, chord.Chord):
        return list(element.pitches)
    return []


def _group_key(element: note.GeneralNote, granularity: str) -> tuple[int | None, float | int | None, float]:
    measure_number = element.measureNumber
    if granularity == "event":
        return (measure_number, round(float(element.offset), 3), round(float(element.offset), 3))

    beat = float(element.beat) if element.beat is not None else None
    if beat is not None and math.isnan(beat):
        beat = None
    beat_group = None if beat is None else int(math.floor(beat - 1e-9) + 1)
    return (measure_number, beat_group, round(float(element.offset), 3))


def _get_local_key_label(measure_number: int | None, key_regions: list[KeyRegion], global_key_label: str) -> str:
    if measure_number is None:
        return global_key_label
    for region in key_regions:
        if region.start_measure <= measure_number <= region.end_measure:
            return region.key
    return global_key_label


def _parse_key_label(key_label: str) -> key.Key:
    tonic, mode = key_label.split(" ", maxsplit=1)
    return key.Key(tonic, mode)


def _harmonic_function(roman_figure: str | None) -> str | None:
    if not roman_figure:
        return None

    primary = roman_figure.split("/")[0]
    dominant_markers = ("V", "vii", "Cad", "cad")
    predominant_markers = ("ii", "iio", "iio", "ii", "IV", "iv", "N", "Ger", "Fr", "It")
    tonic_markers = ("I", "i", "vi", "VI", "iii", "III")

    if primary.startswith(dominant_markers):
        return "dominant"
    if primary.startswith(predominant_markers):
        return "predominant"
    if primary.startswith(tonic_markers):
        return "tonic"
    return "other"


def _collect_bucket_records(score: stream.Score, granularity: str) -> list[dict[str, object]]:
    chordified = score.chordify()
    buckets: "OrderedDict[tuple[int | None, float | int | None, float], dict[str, object]]" = OrderedDict()

    for element in chordified.flatten().notesAndRests:
        if element.isRest:
            continue
        bucket_id = _group_key(element, granularity)
        record = buckets.setdefault(
            bucket_id,
            {
                "measure_number": element.measureNumber,
                "beat": (
                    None
                    if element.beat is None or math.isnan(float(element.beat))
                    else float(element.beat)
                ),
                "offset_ql": float(element.offset),
                "duration_ql": 0.0,
                "observed_pitches": [],
            },
        )
        record["duration_ql"] = max(float(record["duration_ql"]), float(element.duration.quarterLength))
        observed_pitches = record["observed_pitches"]
        if isinstance(observed_pitches, list):
            observed_pitches.extend(_element_pitches(element))
    return list(buckets.values())


def _unique_pitch_classes(pitches: list[note.Pitch]) -> list[int]:
    return sorted({pitch_obj.pitchClass for pitch_obj in pitches})


def _texture_profile(records: list[dict[str, object]]) -> dict[str, float | int | str | bool]:
    if not records:
        return {
            "segment_count": 0,
            "average_observed_pitch_classes": 0.0,
            "max_observed_pitch_classes": 0,
            "sparse_segment_ratio": 0.0,
            "is_implied_harmony": False,
            "inference_strategy": "literal_verticality",
        }

    unique_pitch_class_counts = []
    sparse_count = 0
    for record in records:
        pitches = [pitch_obj for pitch_obj in record["observed_pitches"] if pitch_obj is not None]
        count = len(_unique_pitch_classes(pitches))
        unique_pitch_class_counts.append(count)
        if count <= 2:
            sparse_count += 1

    average_observed_pitch_classes = mean(unique_pitch_class_counts)
    sparse_segment_ratio = sparse_count / len(records)
    is_implied_harmony = average_observed_pitch_classes < 2.2 or sparse_segment_ratio >= 0.65
    return {
        "segment_count": len(records),
        "average_observed_pitch_classes": round(average_observed_pitch_classes, 4),
        "max_observed_pitch_classes": max(unique_pitch_class_counts, default=0),
        "sparse_segment_ratio": round(sparse_segment_ratio, 4),
        "is_implied_harmony": is_implied_harmony,
        "inference_strategy": "implicit_harmony_window" if is_implied_harmony else "literal_verticality",
    }


def _neighbor_indices(records: list[dict[str, object]], center_index: int, max_radius: int = 4) -> list[int]:
    center_record = records[center_index]
    center_measure = center_record["measure_number"]
    center_offset = float(center_record["offset_ql"])
    indices = [center_index]

    for radius in range(1, max_radius + 1):
        for candidate_index in (center_index + radius, center_index - radius):
            if candidate_index < 0 or candidate_index >= len(records):
                continue
            candidate = records[candidate_index]
            candidate_measure = candidate["measure_number"]
            candidate_offset = float(candidate["offset_ql"])
            if center_measure is not None and candidate_measure is not None and abs(candidate_measure - center_measure) > 1:
                continue
            if abs(candidate_offset - center_offset) > 4.0:
                continue
            indices.append(candidate_index)
    return indices


def _analysis_pitches(records: list[dict[str, object]], record_index: int, implied_harmony: bool) -> tuple[list[note.Pitch], str]:
    observed_pitches = [pitch_obj for pitch_obj in records[record_index]["observed_pitches"] if pitch_obj is not None]
    observed_pitch_classes = _unique_pitch_classes(observed_pitches)
    if not implied_harmony or len(observed_pitch_classes) >= 3:
        return observed_pitches, "literal_verticality"

    pooled_pitches: list[note.Pitch] = []
    seen_indices = set()
    for candidate_index in _neighbor_indices(records, record_index):
        if candidate_index in seen_indices:
            continue
        seen_indices.add(candidate_index)
        pooled_pitches.extend(
            pitch_obj
            for pitch_obj in records[candidate_index]["observed_pitches"]
            if pitch_obj is not None
        )
        if len(_unique_pitch_classes(pooled_pitches)) >= 3:
            break

    if not pooled_pitches:
        pooled_pitches = observed_pitches
    return pooled_pitches, "implicit_harmony_window"


def extract_harmonic_segments(
    score: stream.Score,
    key_regions: list[KeyRegion],
    global_key_label: str,
    granularity: str = "beat",
) -> tuple[list[HarmonicSegment], dict[str, float | int | str | bool]]:
    records = _collect_bucket_records(score, granularity)
    texture_profile = _texture_profile(records)
    implied_harmony = bool(texture_profile["is_implied_harmony"])

    segments: list[HarmonicSegment] = []
    for record_index, record in enumerate(records):
        observed_pitches = [pitch_obj for pitch_obj in record["observed_pitches"] if pitch_obj is not None]
        pitches, inference_strategy = _analysis_pitches(records, record_index, implied_harmony)
        if not pitches:
            continue
        working_chord = chord.Chord(pitches)
        local_key_label = _get_local_key_label(record["measure_number"], key_regions, global_key_label)
        local_key = _parse_key_label(local_key_label)
        roman_label = None
        try:
            roman_label = roman.romanNumeralFromChord(working_chord, local_key).figure
        except (TypeError, ValueError, AttributeError):
            roman_label = None

        chord_figure = None
        try:
            chord_figure = harmony.chordSymbolFigureFromChord(working_chord)
        except (TypeError, ValueError, AttributeError):
            chord_figure = None

        segments.append(
            HarmonicSegment(
                measure_number=record["measure_number"],
                beat=record["beat"],
                offset_ql=float(record["offset_ql"]),
                duration_ql=float(record["duration_ql"]),
                pitch_names=sorted({pitch_obj.nameWithOctave for pitch_obj in pitches}, key=lambda value: value),
                pitch_classes=sorted({pitch_obj.pitchClass for pitch_obj in pitches}),
                bass=working_chord.bass().nameWithOctave if working_chord.bass() else None,
                soprano=working_chord.sortAscending().pitches[-1].nameWithOctave if working_chord.pitches else None,
                root=working_chord.root().name if working_chord.root() else None,
                quality=working_chord.quality,
                inversion=working_chord.inversion(),
                has_seventh=working_chord.seventh is not None,
                chord_figure=chord_figure,
                roman_numeral=roman_label,
                harmonic_function=_harmonic_function(roman_label),
                key=local_key_label,
                observed_pitch_names=sorted({pitch_obj.nameWithOctave for pitch_obj in observed_pitches}, key=lambda value: value),
                inference_strategy=inference_strategy,
            )
        )
    return segments, texture_profile


def estimate_harmonic_rhythm(segments: list[HarmonicSegment]) -> dict[str, float | int]:
    if not segments:
        return {
            "total_segments": 0,
            "changes": 0,
            "changes_per_measure": 0.0,
            "average_segment_duration_ql": 0.0,
        }

    changes = 0
    measures = {segment.measure_number for segment in segments if segment.measure_number is not None}
    previous_label = None
    for segment in segments:
        label = segment.roman_numeral or segment.chord_figure or segment.root
        if previous_label is not None and label != previous_label:
            changes += 1
        previous_label = label

    return {
        "total_segments": len(segments),
        "changes": changes,
        "changes_per_measure": round(changes / max(1, len(measures)), 3),
        "average_segment_duration_ql": round(
            sum(segment.duration_ql for segment in segments) / len(segments),
            3,
        ),
    }


def detect_secondary_functions(segments: list[HarmonicSegment]) -> list[HarmonicSegment]:
    secondary_segments = []
    for segment in segments:
        roman_label = segment.roman_numeral or ""
        if "/" in roman_label:
            secondary_segments.append(segment)
            continue
        if roman_label.startswith(("viio/", "viio/", "vii/")):
            secondary_segments.append(segment)
    return secondary_segments
