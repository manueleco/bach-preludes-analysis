from __future__ import annotations

from collections import Counter

from music21 import interval, key, note

from bach_preludes_analysis.models import HarmonicSegment, VoiceLeadingObservation


def _note_from_name(name: str | None) -> note.Note | None:
    if not name:
        return None
    return note.Note(name)


def _motion(first: note.Note | None, second: note.Note | None) -> int:
    if first is None or second is None:
        return 0
    if second.pitch.midi > first.pitch.midi:
        return 1
    if second.pitch.midi < first.pitch.midi:
        return -1
    return 0


def _local_key(key_label: str | None) -> key.Key | None:
    if not key_label:
        return None
    tonic, mode = key_label.split(" ", maxsplit=1)
    return key.Key(tonic, mode)


def analyze_voice_leading(
    segments: list[HarmonicSegment],
) -> tuple[dict[str, float | int | list[tuple[str, int]]], list[VoiceLeadingObservation]]:
    if len(segments) < 2:
        return {"parallel_perfects": 0, "contrary_motion_rate": 0.0, "common_bass_moves": []}, []

    bass_motion_counter: Counter[str] = Counter()
    contrary_motion_count = 0
    parallel_perfects = 0
    total_motion_pairs = 0
    observations: list[VoiceLeadingObservation] = []

    for first_segment, second_segment in zip(segments, segments[1:]):
        first_bass = _note_from_name(first_segment.bass)
        second_bass = _note_from_name(second_segment.bass)
        first_soprano = _note_from_name(first_segment.soprano)
        second_soprano = _note_from_name(second_segment.soprano)

        if first_bass and second_bass:
            bass_motion_counter[interval.Interval(first_bass, second_bass).simpleName] += 1

        bass_motion = _motion(first_bass, second_bass)
        soprano_motion = _motion(first_soprano, second_soprano)
        if bass_motion != 0 and soprano_motion != 0:
            total_motion_pairs += 1
            if bass_motion == -soprano_motion:
                contrary_motion_count += 1
            elif bass_motion == soprano_motion and first_bass and first_soprano and second_bass and second_soprano:
                first_outer = interval.Interval(first_bass, first_soprano).simpleName
                second_outer = interval.Interval(second_bass, second_soprano).simpleName
                if first_outer in {"P1", "P5", "P8"} and second_outer in {"P1", "P5", "P8"}:
                    parallel_perfects += 1
                    observations.append(
                        VoiceLeadingObservation(
                            measure_number=second_segment.measure_number,
                            beat=second_segment.beat,
                            category="parallel_perfect",
                            explanation="Las voces extremas se mueven en la misma direccion manteniendo una consonancia perfecta.",
                        )
                    )

        local_key = _local_key(first_segment.key)
        if local_key and first_soprano and second_soprano:
            if first_soprano.pitch.pitchClass == local_key.pitchFromDegree(7).pitchClass and second_soprano.pitch.pitchClass == local_key.tonic.pitchClass:
                observations.append(
                    VoiceLeadingObservation(
                        measure_number=second_segment.measure_number,
                        beat=second_segment.beat,
                        category="leading_tone_resolution",
                        explanation="La sensible en la voz superior resuelve a la tonica.",
                    )
                )

        if first_segment.has_seventh and first_soprano and second_soprano:
            if second_soprano.pitch.midi < first_soprano.pitch.midi and abs(second_soprano.pitch.midi - first_soprano.pitch.midi) in (1, 2):
                observations.append(
                    VoiceLeadingObservation(
                        measure_number=second_segment.measure_number,
                        beat=second_segment.beat,
                        category="seventh_resolution",
                        explanation="El movimiento descendente por grado conjunto es compatible con la resolucion de la septima del acorde.",
                    )
                )

    contrary_motion_rate = round(contrary_motion_count / max(1, total_motion_pairs), 4)
    return (
        {
            "parallel_perfects": parallel_perfects,
            "contrary_motion_rate": contrary_motion_rate,
            "common_bass_moves": bass_motion_counter.most_common(5),
        },
        observations,
    )
