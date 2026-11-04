from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from bach_preludes_analysis.analysis.keys import analyze_global_key
from bach_preludes_analysis.audio_pipeline import analyze_audio
from bach_preludes_analysis.config import DEFAULT_CASE_STUDY_ID
from bach_preludes_analysis.corpus_profiles import resolve_audio_input_dir, resolve_symbolic_input_dir
from bach_preludes_analysis.io import discover_audio_paths, discover_score_paths, infer_piece_id, load_score
from bach_preludes_analysis.models import ScoreAudioValidation


def _score_pitch_class_profile(score) -> np.ndarray:
    profile = np.zeros(12, dtype=float)
    for element in score.recurse().notes:
        duration = float(getattr(element, "quarterLength", 1.0) or 1.0)
        if hasattr(element, "pitch"):
            profile[int(element.pitch.pitchClass)] += duration
            continue
        if hasattr(element, "pitches"):
            for pitch in element.pitches:
                profile[int(pitch.pitchClass)] += duration
    total = float(profile.sum())
    if total <= 0.0:
        return profile
    return profile / total


def _audio_pitch_class_profile(analysis) -> np.ndarray | None:
    chroma_profile = analysis.tonal.get("chroma_profile")
    if not chroma_profile:
        return None
    vector = np.asarray(chroma_profile, dtype=float)
    total = float(vector.sum())
    if total <= 0.0:
        return None
    return vector / total


def _cosine_similarity(left: np.ndarray, right: np.ndarray) -> float | None:
    left_norm = float(np.linalg.norm(left))
    right_norm = float(np.linalg.norm(right))
    if left_norm <= 0.0 or right_norm <= 0.0:
        return None
    return float(np.dot(left, right) / (left_norm * right_norm))


def _key_label_from_audio(analysis) -> str | None:
    if analysis.estimated_key is None:
        return None
    if analysis.estimated_scale is None:
        return analysis.estimated_key
    return f"{analysis.estimated_key} {analysis.estimated_scale}"


def _validation_status(piece_id_match: bool, pitch_class_similarity: float | None, score_key: str, audio_key: str | None) -> tuple[str, list[str]]:
    notes: list[str] = []
    if not piece_id_match:
        notes.append("Los nombres inferidos de score y audio no coinciden.")
    if audio_key is not None and score_key.lower() != audio_key.lower():
        notes.append("La tonalidad estimada desde audio no coincide exactamente con la del score.")
    if pitch_class_similarity is None:
        notes.append("No fue posible calcular similitud cromatica entre score y audio.")
    elif pitch_class_similarity < 0.75:
        notes.append("La similitud cromatica es baja; revisar emparejamiento o calidad del score/OMR.")
    elif pitch_class_similarity < 0.9:
        notes.append("La similitud cromatica es razonable, pero conviene revisar manualmente.")

    if piece_id_match and pitch_class_similarity is not None and pitch_class_similarity >= 0.9:
        return "pass", notes
    if piece_id_match and pitch_class_similarity is not None and pitch_class_similarity >= 0.75:
        return "review", notes
    return "warn", notes


def validate_score_against_audio(
    score_path: Path,
    audio_path: Path,
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
    audio_profile: str = "single_interpreter_reference",
    backend: str = "auto",
) -> ScoreAudioValidation:
    score = load_score(score_path)
    score_key_obj = analyze_global_key(score)
    score_key = f"{score_key_obj.tonicPitchNameWithCase} {score_key_obj.mode}"
    score_piece_id = infer_piece_id(score_path, case_study_id=case_study_id)
    audio_piece_id = infer_piece_id(audio_path, case_study_id=case_study_id)

    audio_analysis = analyze_audio(
        audio_path,
        backend=backend,
        corpus_profile=audio_profile,
        case_study_id=case_study_id,
    )
    audio_profile_vector = _audio_pitch_class_profile(audio_analysis)
    if audio_profile_vector is None and backend != "librosa":
        audio_analysis = analyze_audio(
            audio_path,
            backend="librosa",
            corpus_profile=audio_profile,
            case_study_id=case_study_id,
        )
        audio_profile_vector = _audio_pitch_class_profile(audio_analysis)

    score_profile = _score_pitch_class_profile(score)
    similarity = _cosine_similarity(score_profile, audio_profile_vector) if audio_profile_vector is not None else None
    audio_key = _key_label_from_audio(audio_analysis)
    status, notes = _validation_status(
        piece_id_match=(score_piece_id == audio_piece_id),
        pitch_class_similarity=similarity,
        score_key=score_key,
        audio_key=audio_key,
    )

    return ScoreAudioValidation(
        piece_id=score_piece_id,
        score_path=score_path,
        audio_path=audio_path,
        case_study_id=case_study_id,
        score_global_key=score_key,
        audio_estimated_key=audio_key,
        piece_id_match=(score_piece_id == audio_piece_id),
        pitch_class_similarity=(round(similarity, 6) if similarity is not None else None),
        status=status,
        notes=notes,
    )


def validate_case_study_pairs(
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
    symbolic_profile: str = "official_curated",
    audio_profile: str = "single_interpreter_reference",
    backend: str = "auto",
    symbolic_input_dir: Path | None = None,
    audio_input_dir: Path | None = None,
) -> list[ScoreAudioValidation]:
    score_dir = resolve_symbolic_input_dir(
        profile_id=symbolic_profile,
        explicit_input_dir=symbolic_input_dir,
        case_study_id=case_study_id,
    )
    audio_dir = resolve_audio_input_dir(
        profile_id=audio_profile,
        explicit_input_dir=audio_input_dir,
        case_study_id=case_study_id,
    )

    score_map = {infer_piece_id(path, case_study_id=case_study_id): path for path in discover_score_paths(score_dir)}
    audio_map = {infer_piece_id(path, case_study_id=case_study_id): path for path in discover_audio_paths(audio_dir)}
    validations: list[ScoreAudioValidation] = []
    for piece_id in sorted(set(score_map) & set(audio_map)):
        validations.append(
            validate_score_against_audio(
                score_map[piece_id],
                audio_map[piece_id],
                case_study_id=case_study_id,
                audio_profile=audio_profile,
                backend=backend,
            )
        )
    return validations


def save_validations(validations: list[ScoreAudioValidation], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "score_audio_validation.json"
    csv_path = output_dir / "score_audio_validation.csv"

    json_path.write_text(json.dumps([validation.to_dict() for validation in validations], indent=2), encoding="utf-8")
    pd.DataFrame([validation.to_dict() for validation in validations]).to_csv(csv_path, index=False)
    return json_path, csv_path
