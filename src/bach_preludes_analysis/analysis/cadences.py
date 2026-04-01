from __future__ import annotations

from collections import defaultdict

from bach_preludes_analysis.models import CadenceEvent, HarmonicSegment


def _group_measure_segments(segments: list[HarmonicSegment]) -> dict[int, list[HarmonicSegment]]:
    grouped: dict[int, list[HarmonicSegment]] = defaultdict(list)
    for segment in segments:
        if segment.measure_number is None:
            continue
        grouped[segment.measure_number].append(segment)
    return dict(grouped)


def _is_tonic(segment: HarmonicSegment | None) -> bool:
    if not segment or not segment.roman_numeral:
        return False
    return segment.roman_numeral.startswith(("I", "i"))


def _is_dominant(segment: HarmonicSegment | None) -> bool:
    if not segment or not segment.roman_numeral:
        return False
    return segment.roman_numeral.startswith(("V", "vii"))


def _is_predominant(segment: HarmonicSegment | None) -> bool:
    if not segment or not segment.roman_numeral:
        return False
    return segment.roman_numeral.startswith(("ii", "IV", "iv", "N", "Ger", "Fr", "It"))


def detect_cadences(segments: list[HarmonicSegment]) -> list[CadenceEvent]:
    grouped = _group_measure_segments(segments)
    ordered_measures = sorted(grouped)
    cadence_events: list[CadenceEvent] = []

    previous_terminal: HarmonicSegment | None = None
    for measure_number in ordered_measures:
        measure_segments = sorted(grouped[measure_number], key=lambda segment: segment.offset_ql)
        final_segment = measure_segments[-1]
        penult_segment = measure_segments[-2] if len(measure_segments) > 1 else previous_terminal
        cadence_type = None
        explanation = None
        confidence = 0.55

        if _is_dominant(penult_segment) and _is_tonic(final_segment):
            if final_segment.inversion == 0 and final_segment.soprano and final_segment.root:
                cadence_type = "PAC"
                explanation = "Movimiento dominante-tonica con tonica en posicion estable al cierre del compas."
                confidence = 0.8
            else:
                cadence_type = "IAC"
                explanation = "Movimiento dominante-tonica sin todas las condiciones de una autentica perfecta."
                confidence = 0.7
        elif _is_dominant(penult_segment) and final_segment.roman_numeral and final_segment.roman_numeral.startswith(
            ("vi", "VI")
        ):
            cadence_type = "deceptive"
            explanation = "La dominante resuelve hacia VI o vi en lugar de cerrar en tonica."
            confidence = 0.78
        elif _is_predominant(penult_segment) and _is_dominant(final_segment):
            cadence_type = "half"
            explanation = "El cierre del compas termina en dominante y sugiere semicadencia."
            confidence = 0.72
        elif penult_segment and penult_segment.roman_numeral and penult_segment.roman_numeral.startswith(
            ("IV", "iv")
        ) and _is_tonic(final_segment):
            cadence_type = "plagal"
            explanation = "El cierre IV-I produce un gesto plagal."
            confidence = 0.64
        elif penult_segment and penult_segment.roman_numeral == "iv6" and final_segment.roman_numeral == "V":
            cadence_type = "phrygian"
            explanation = "La progresion iv6-V es compatible con una semicadencia frigia."
            confidence = 0.75

        if cadence_type:
            cadence_events.append(
                CadenceEvent(
                    cadence_type=cadence_type,
                    measure_number=final_segment.measure_number,
                    beat=final_segment.beat,
                    key=final_segment.key,
                    confidence=confidence,
                    explanation=explanation or "Cadential heuristic match.",
                )
            )
        previous_terminal = final_segment
    return cadence_events
