from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class KeyRegion:
    start_measure: int
    end_measure: int
    key: str
    correlation: float | None = None


@dataclass
class HarmonicSegment:
    measure_number: int | None
    beat: float | None
    offset_ql: float
    duration_ql: float
    pitch_names: list[str]
    pitch_classes: list[int]
    bass: str | None
    soprano: str | None
    root: str | None
    quality: str | None
    inversion: int | None
    has_seventh: bool
    chord_figure: str | None
    roman_numeral: str | None
    harmonic_function: str | None
    key: str | None
    observed_pitch_names: list[str] = field(default_factory=list)
    inference_strategy: str | None = None


@dataclass
class CadenceEvent:
    cadence_type: str
    measure_number: int | None
    beat: float | None
    key: str | None
    confidence: float
    explanation: str


@dataclass
class NonChordToneObservation:
    measure_number: int | None
    beat: float | None
    pitch: str
    voice: str
    classification: str
    explanation: str


@dataclass
class SequenceObservation:
    pattern: str
    occurrences: int
    measures: list[int]
    explanation: str


@dataclass
class VoiceLeadingObservation:
    measure_number: int | None
    beat: float | None
    category: str
    explanation: str


@dataclass
class PieceAnalysis:
    piece_id: str
    source_path: Path
    measure_count: int
    global_key: str
    case_study_id: str = "bach_cello_suites"
    case_study_label: str = "Bach cello suite preludes"
    corpus_profile_id: str = "official_curated"
    corpus_profile_label: str = "Official curated symbolic corpus"
    reliability: dict[str, str] = field(default_factory=dict)
    source_context: dict[str, Any] = field(default_factory=dict)
    key_regions: list[KeyRegion] = field(default_factory=list)
    segments: list[HarmonicSegment] = field(default_factory=list)
    harmonic_rhythm: dict[str, Any] = field(default_factory=dict)
    cadences: list[CadenceEvent] = field(default_factory=list)
    secondary_functions: list[HarmonicSegment] = field(default_factory=list)
    non_chord_tones: list[NonChordToneObservation] = field(default_factory=list)
    sequences: list[SequenceObservation] = field(default_factory=list)
    chromaticism: dict[str, Any] = field(default_factory=dict)
    texture_profile: dict[str, Any] = field(default_factory=dict)
    voice_leading: dict[str, Any] = field(default_factory=dict)
    voice_leading_events: list[VoiceLeadingObservation] = field(default_factory=list)
    summaries: dict[str, str] = field(default_factory=dict)

    @property
    def prelude_id(self) -> str:
        return self.piece_id

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["source_path"] = str(self.source_path)
        payload["prelude_id"] = self.piece_id
        return payload


@dataclass
class AudioAnalysis:
    piece_id: str
    source_path: Path
    backend: str
    duration_seconds: float
    sample_rate: int
    tempo_bpm: float | None = None
    beat_count: int = 0
    beat_confidence: float | None = None
    estimated_key: str | None = None
    estimated_scale: str | None = None
    key_strength: float | None = None
    case_study_id: str = "bach_cello_suites"
    case_study_label: str = "Bach cello suite preludes"
    corpus_profile_id: str = "single_interpreter_reference"
    corpus_profile_label: str = "Single-interpreter reference recordings"
    reliability: dict[str, str] = field(default_factory=dict)
    source_context: dict[str, Any] = field(default_factory=dict)
    metering: dict[str, Any] = field(default_factory=dict)
    spectral: dict[str, Any] = field(default_factory=dict)
    tonal: dict[str, Any] = field(default_factory=dict)
    expression: dict[str, Any] = field(default_factory=dict)
    summaries: dict[str, str] = field(default_factory=dict)

    @property
    def prelude_id(self) -> str:
        return self.piece_id

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["source_path"] = str(self.source_path)
        payload["prelude_id"] = self.piece_id
        return payload


@dataclass
class ScoreAudioValidation:
    piece_id: str
    score_path: Path
    audio_path: Path
    case_study_id: str
    score_global_key: str
    audio_estimated_key: str | None
    piece_id_match: bool
    pitch_class_similarity: float | None
    status: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["score_path"] = str(self.score_path)
        payload["audio_path"] = str(self.audio_path)
        return payload


@dataclass
class ComparisonResult:
    feature_rows: list[dict[str, Any]]
    similarity_matrix: dict[str, dict[str, float]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_rows": self.feature_rows,
            "similarity_matrix": self.similarity_matrix,
        }


PreludeAnalysis = PieceAnalysis
