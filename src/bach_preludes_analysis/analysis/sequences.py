from __future__ import annotations

from collections import defaultdict

from bach_preludes_analysis.models import HarmonicSegment, SequenceObservation


def detect_recurrent_progressions(
    segments: list[HarmonicSegment],
    min_length: int = 3,
    max_length: int = 4,
) -> list[SequenceObservation]:
    roman_labels = [segment.roman_numeral for segment in segments]
    observations: list[SequenceObservation] = []

    for length in range(max_length, min_length - 1, -1):
        bucket: dict[tuple[str, ...], list[int]] = defaultdict(list)
        for index in range(len(roman_labels) - length + 1):
            pattern = tuple(label for label in roman_labels[index : index + length] if label)
            if len(pattern) != length:
                continue
            bucket[pattern].append(index)

        for pattern, positions in bucket.items():
            if len(positions) < 2:
                continue
            measures = []
            for position in positions:
                measure_number = segments[position].measure_number
                if measure_number is not None:
                    measures.append(measure_number)
            observations.append(
                SequenceObservation(
                    pattern=" - ".join(pattern),
                    occurrences=len(positions),
                    measures=sorted(set(measures)),
                    explanation="Patron recurrente de numerales romanos repetido en mas de un punto del preludio.",
                )
            )
    observations.sort(key=lambda item: (-item.occurrences, item.pattern))
    return observations
