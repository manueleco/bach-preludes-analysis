from __future__ import annotations

from collections.abc import Iterable

from music21.analysis.discrete import DiscreteAnalysisException
from music21 import key, stream

from bach_preludes_analysis.config import DEFAULT_KEY_WINDOW_MEASURES
from bach_preludes_analysis.models import KeyRegion


def _key_label(key_obj: key.Key) -> str:
    return f"{key_obj.tonicPitchNameWithCase} {key_obj.mode}"


def _measure_count(score: stream.Score) -> int:
    measures = []
    for part in score.parts if score.parts else [score]:
        measures.extend(measure.measureNumber for measure in part.getElementsByClass(stream.Measure))
    return max((number for number in measures if number is not None), default=0)


def _fallback_key() -> key.Key:
    return key.Key("C")


def _safe_analyze_key(score_like: stream.Stream, fallback: key.Key | None = None) -> key.Key:
    try:
        return score_like.analyze("key")
    except (DiscreteAnalysisException, AttributeError, ValueError):
        return fallback or _fallback_key()


def analyze_global_key(score: stream.Score) -> key.Key:
    return _safe_analyze_key(score)


def analyze_key_regions(
    score: stream.Score,
    window_measures: int = DEFAULT_KEY_WINDOW_MEASURES,
) -> list[KeyRegion]:
    detected_global_key = analyze_global_key(score)
    total_measures = _measure_count(score)
    if total_measures == 0:
        return [KeyRegion(start_measure=1, end_measure=1, key=_key_label(detected_global_key))]

    assignments: list[tuple[int, str, float | None]] = []
    radius = max(1, window_measures // 2)
    for measure_number in range(1, total_measures + 1):
        start_measure = max(1, measure_number - radius)
        end_measure = min(total_measures, start_measure + window_measures - 1)
        start_measure = max(1, end_measure - window_measures + 1)
        excerpt = score.measures(start_measure, end_measure)
        local_key = _safe_analyze_key(excerpt, fallback=detected_global_key)
        assignments.append(
            (
                measure_number,
                _key_label(local_key),
                getattr(local_key, "correlationCoefficient", None),
            )
        )

    regions: list[KeyRegion] = []
    for measure_number, label, correlation in assignments:
        if not regions or regions[-1].key != label:
            regions.append(
                KeyRegion(
                    start_measure=measure_number,
                    end_measure=measure_number,
                    key=label,
                    correlation=correlation,
                )
            )
            continue
        regions[-1].end_measure = measure_number
        if correlation is not None:
            regions[-1].correlation = correlation
    return regions


def key_for_measure(measure_number: int | None, key_regions: Iterable[KeyRegion], fallback: str) -> str:
    if measure_number is None:
        return fallback
    for region in key_regions:
        if region.start_measure <= measure_number <= region.end_measure:
            return region.key
    return fallback
