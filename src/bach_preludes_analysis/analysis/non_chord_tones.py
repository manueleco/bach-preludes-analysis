from __future__ import annotations

from music21 import chord, interval, note, stream

from bach_preludes_analysis.models import HarmonicSegment, NonChordToneObservation


def _is_step_motion(first_pitch: note.Pitch, second_pitch: note.Pitch) -> bool:
    return abs(first_pitch.midi - second_pitch.midi) in (1, 2)


def _active_segment(offset_ql: float, segments: list[HarmonicSegment]) -> HarmonicSegment | None:
    for segment in segments:
        end_offset = segment.offset_ql + max(segment.duration_ql, 0.25)
        if segment.offset_ql <= offset_ql < end_offset:
            return segment
    return segments[-1] if segments else None


def _voice_label(part_index: int) -> str:
    return f"part_{part_index + 1}"


def detect_non_chord_tones(
    score: stream.Score,
    segments: list[HarmonicSegment],
) -> list[NonChordToneObservation]:
    observations: list[NonChordToneObservation] = []
    parts = list(score.parts) if score.parts else [score]

    for part_index, part in enumerate(parts):
        melodic_notes = [element for element in part.flatten().notes if isinstance(element, note.Note)]
        for note_index in range(1, len(melodic_notes) - 1):
            current_note = melodic_notes[note_index]
            previous_note = melodic_notes[note_index - 1]
            next_note = melodic_notes[note_index + 1]
            segment = _active_segment(float(current_note.offset), segments)
            if not segment or current_note.pitch.pitchClass in segment.pitch_classes:
                continue

            current_pitch = current_note.pitch
            previous_pitch = previous_note.pitch
            next_pitch = next_note.pitch
            previous_segment = _active_segment(float(previous_note.offset), segments)
            next_segment = _active_segment(float(next_note.offset), segments)
            classification = "unclassified"
            explanation = "Nota ajena al acorde detectada por fuera del conjunto de alturas del segmento."

            prev_is_chord_tone = previous_segment is not None and previous_pitch.pitchClass in previous_segment.pitch_classes
            next_is_chord_tone = next_segment is not None and next_pitch.pitchClass in next_segment.pitch_classes

            if (
                prev_is_chord_tone
                and next_is_chord_tone
                and _is_step_motion(previous_pitch, current_pitch)
                and _is_step_motion(current_pitch, next_pitch)
                and (current_pitch.midi - previous_pitch.midi) * (next_pitch.midi - current_pitch.midi) > 0
            ):
                classification = "passing_tone"
                explanation = "Paso entre dos notas del acorde por movimiento conjunto en la misma direccion."
            elif (
                prev_is_chord_tone
                and next_is_chord_tone
                and previous_pitch.midi == next_pitch.midi
                and _is_step_motion(previous_pitch, current_pitch)
            ):
                classification = "neighbor_tone"
                explanation = "Movimiento de bordadura alrededor de una nota estructural."
            elif current_note.tie is not None and next_is_chord_tone and next_pitch.midi < current_pitch.midi:
                classification = "suspension"
                explanation = "La nota prolongada crea disonancia y resuelve descendiendo por paso."
            elif next_segment and current_pitch.pitchClass in next_segment.pitch_classes and next_pitch.midi == current_pitch.midi:
                classification = "anticipation"
                explanation = "La altura del acorde siguiente aparece antes del cambio armonico."
            elif (
                prev_is_chord_tone
                and next_is_chord_tone
                and not _is_step_motion(previous_pitch, current_pitch)
                and _is_step_motion(current_pitch, next_pitch)
                and (current_note.beat or 0) <= 1.5
            ):
                classification = "appoggiatura"
                explanation = "Entrada por salto y resolucion por paso en posicion acentuada."

            observations.append(
                NonChordToneObservation(
                    measure_number=current_note.measureNumber,
                    beat=float(current_note.beat) if current_note.beat is not None else None,
                    pitch=current_note.nameWithOctave,
                    voice=_voice_label(part_index),
                    classification=classification,
                    explanation=explanation,
                )
            )

    return observations
