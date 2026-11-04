from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from music21 import key, note, stream

from bach_preludes_analysis.audio_pipeline import analyze_audio_corpus
from bach_preludes_analysis.case_studies import get_case_study
from bach_preludes_analysis.catalog import catalog_row_for_piece_id, load_catalog_rows
from bach_preludes_analysis.config import DEFAULT_CASE_STUDY_ID
from bach_preludes_analysis.corpus_profiles import available_paths_for_profile
from bach_preludes_analysis.io import infer_piece_id, load_score
from bach_preludes_analysis.models import AudioAnalysis, PieceAnalysis
from bach_preludes_analysis.pipeline import analyze_score


DEFAULT_SYMBOLIC_PROFILE_PRIORITY = (
    "official_curated",
    "audiveris_intermediate",
    "mutopia_reference",
    "kern_reference",
)


def _scale_pitch_classes(key_label: str) -> set[int]:
    tonic, mode = key_label.split(" ", maxsplit=1)
    local_key = key.Key(tonic, mode)
    return {pitch_obj.pitchClass for pitch_obj in local_key.getScale().pitches[:7]}


def _piece_title(piece_id: str, case_study_id: str = DEFAULT_CASE_STUDY_ID) -> str:
    row = catalog_row_for_piece_id(piece_id, case_study_id=case_study_id)
    if row is None:
        return piece_id
    return f"{row['title']} - {row['movement_title']} ({row['catalog_number']})"


def best_available_symbolic_assets(
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
    profile_priority: tuple[str, ...] = DEFAULT_SYMBOLIC_PROFILE_PRIORITY,
) -> tuple[list[dict[str, str]], pd.DataFrame]:
    piece_ids = [row["piece_id"] for row in load_catalog_rows(case_study_id)]
    candidates_by_piece: dict[str, list[tuple[str, Path]]] = defaultdict(list)
    for profile_id in profile_priority:
        for path in available_paths_for_profile(profile_id, case_study_id=case_study_id):
            piece_id = infer_piece_id(path, case_study_id=case_study_id)
            candidates_by_piece[piece_id].append((profile_id, path))

    selected: list[dict[str, str]] = []
    coverage_rows: list[dict[str, str]] = []
    for piece_id in piece_ids:
        title = _piece_title(piece_id, case_study_id=case_study_id)
        candidate = next(iter(candidates_by_piece.get(piece_id, [])), None)
        if candidate is None:
            coverage_rows.append(
                {
                    "piece_id": piece_id,
                    "title": title,
                    "status": "missing",
                    "source_profile": "",
                    "source_path": "",
                }
            )
            continue
        profile_id, path = candidate
        selected.append(
            {
                "piece_id": piece_id,
                "source_profile": profile_id,
                "source_path": str(path),
            }
        )
        coverage_rows.append(
            {
                "piece_id": piece_id,
                "title": title,
                "status": "available",
                "source_profile": profile_id,
                "source_path": str(path),
            }
        )
    return selected, pd.DataFrame(coverage_rows)


def analyze_best_available_symbolic_case_study(
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
    profile_priority: tuple[str, ...] = DEFAULT_SYMBOLIC_PROFILE_PRIORITY,
    segmentation: str = "beat",
) -> tuple[list[PieceAnalysis], pd.DataFrame]:
    selected_assets, coverage_table = best_available_symbolic_assets(
        case_study_id=case_study_id,
        profile_priority=profile_priority,
    )
    analyses: list[PieceAnalysis] = []
    for item in selected_assets:
        analyses.append(
            analyze_score(
                Path(item["source_path"]),
                segmentation=segmentation,
                corpus_profile=item["source_profile"],
                case_study_id=case_study_id,
            )
        )
    analyses.sort(key=lambda analysis: analysis.piece_id)
    return analyses, coverage_table


def analyze_reference_audio_case_study(
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
    backend: str = "librosa",
) -> list[AudioAnalysis]:
    analyses = analyze_audio_corpus(
        corpus_profile="single_interpreter_reference",
        case_study_id=case_study_id,
        backend=backend,
    )
    analyses.sort(key=lambda analysis: analysis.piece_id)
    return analyses


def local_key_regions_table(analysis: PieceAnalysis) -> pd.DataFrame:
    rows = [
        {
            "piece_id": analysis.piece_id,
            "start_measure": region.start_measure,
            "end_measure": region.end_measure,
            "key": region.key,
            "correlation": region.correlation,
        }
        for region in analysis.key_regions
    ]
    return pd.DataFrame(rows)


def cadences_table(analysis: PieceAnalysis) -> pd.DataFrame:
    rows = [
        {
            "piece_id": analysis.piece_id,
            "measure": cadence.measure_number,
            "beat": cadence.beat,
            "cadence_type": cadence.cadence_type,
            "key": cadence.key,
            "confidence": cadence.confidence,
            "explanation": cadence.explanation,
        }
        for cadence in analysis.cadences
    ]
    return pd.DataFrame(rows)


def _count_measure_non_chord_tones(analysis: PieceAnalysis) -> Counter:
    counter: Counter = Counter()
    for observation in analysis.non_chord_tones:
        if observation.measure_number is not None:
            counter[observation.measure_number] += 1
    return counter


def tension_hotspots_table(analysis: PieceAnalysis, top_n: int = 10) -> pd.DataFrame:
    diatonic_pitch_classes = _scale_pitch_classes(analysis.global_key)
    non_chord_tones_by_measure = _count_measure_non_chord_tones(analysis)
    rows: list[dict[str, object]] = []
    for segment in analysis.segments:
        tension = 0.0
        reasons: list[str] = []
        chromatic_pitch_classes = [pc for pc in segment.pitch_classes if pc not in diatonic_pitch_classes]
        if chromatic_pitch_classes:
            tension += 0.9 * len(chromatic_pitch_classes)
            reasons.append(f"cromatismo={len(chromatic_pitch_classes)}")
        if segment.harmonic_function == "dominant":
            tension += 0.8
            reasons.append("funcion_dominante")
        if segment.has_seventh:
            tension += 0.45
            reasons.append("septima")
        roman_label = segment.roman_numeral or ""
        if any(symbol in roman_label for symbol in ("/", "#", "b", "-", "+", "o")):
            tension += 0.8
            reasons.append("alteracion_o_tonicizacion")
        nct_count = non_chord_tones_by_measure.get(segment.measure_number, 0)
        if nct_count:
            tension += min(1.0, 0.25 * nct_count)
            reasons.append(f"nct={nct_count}")
        if analysis.texture_profile.get("is_implied_harmony", False):
            tension += 0.15
            reasons.append("armonía_implicita")
        rows.append(
            {
                "piece_id": analysis.piece_id,
                "measure": segment.measure_number,
                "beat": segment.beat,
                "key": segment.key,
                "roman": segment.roman_numeral,
                "function": segment.harmonic_function,
                "chord": segment.chord_figure,
                "tension_score": round(float(tension), 3),
                "reasons": ", ".join(reasons) or "sin marcadores fuertes",
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values(["tension_score", "measure", "beat"], ascending=[False, True, True]).head(top_n).reset_index(drop=True)


def pattern_table_within_piece(analysis: PieceAnalysis, top_n: int = 10) -> pd.DataFrame:
    rows = [
        {
            "piece_id": analysis.piece_id,
            "pattern": observation.pattern,
            "occurrences": observation.occurrences,
            "measures": ", ".join(str(number) for number in observation.measures),
            "explanation": observation.explanation,
        }
        for observation in analysis.sequences[:top_n]
    ]
    return pd.DataFrame(rows)


def cross_piece_pattern_table(
    analyses: list[PieceAnalysis],
    min_length: int = 3,
    max_length: int = 4,
    top_n: int = 15,
) -> pd.DataFrame:
    pattern_map: dict[tuple[str, ...], dict[str, object]] = {}
    for analysis in analyses:
        roman_labels = [segment.roman_numeral for segment in analysis.segments if segment.roman_numeral]
        measure_lookup = [segment.measure_number for segment in analysis.segments if segment.roman_numeral]
        for length in range(max_length, min_length - 1, -1):
            for index in range(len(roman_labels) - length + 1):
                pattern = tuple(roman_labels[index : index + length])
                entry = pattern_map.setdefault(
                    pattern,
                    {
                        "pattern": " - ".join(pattern),
                        "piece_ids": set(),
                        "occurrences": 0,
                        "locations": [],
                    },
                )
                entry["piece_ids"].add(analysis.piece_id)
                entry["occurrences"] += 1
                start_measure = measure_lookup[index]
                entry["locations"].append(f"{analysis.piece_id}: m. {start_measure}")

    rows: list[dict[str, object]] = []
    for item in pattern_map.values():
        piece_ids = sorted(item["piece_ids"])
        if len(piece_ids) < 2:
            continue
        rows.append(
            {
                "pattern": item["pattern"],
                "piece_count": len(piece_ids),
                "pieces": ", ".join(piece_ids),
                "occurrences": item["occurrences"],
                "sample_locations": "; ".join(item["locations"][:4]),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values(["piece_count", "occurrences"], ascending=[False, False]).head(top_n).reset_index(drop=True)


def symbolic_comparison_table(analyses: list[PieceAnalysis]) -> pd.DataFrame:
    rows = []
    for analysis in analyses:
        rows.append(
            {
                "piece_id": analysis.piece_id,
                "title": _piece_title(analysis.piece_id, analysis.case_study_id),
                "source_profile": analysis.corpus_profile_id,
                "global_key": analysis.global_key,
                "local_key_regions": len(analysis.key_regions),
                "cadences": len(analysis.cadences),
                "secondary_functions": len(analysis.secondary_functions),
                "non_chord_tones": len(analysis.non_chord_tones),
                "sequence_patterns": len(analysis.sequences),
                "chromatic_density": analysis.chromaticism.get("chromatic_density"),
                "dissonance_density": analysis.chromaticism.get("dissonance_density"),
                "contrary_motion_rate": analysis.voice_leading.get("contrary_motion_rate"),
            }
        )
    return pd.DataFrame(rows).sort_values("piece_id").reset_index(drop=True) if rows else pd.DataFrame()


def audio_comparison_table(audio_analyses: list[AudioAnalysis]) -> pd.DataFrame:
    rows = []
    for analysis in audio_analyses:
        rows.append(
            {
                "piece_id": analysis.piece_id,
                "title": _piece_title(analysis.piece_id, analysis.case_study_id),
                "duration_seconds": analysis.duration_seconds,
                "tempo_bpm": analysis.tempo_bpm,
                "estimated_key": f"{analysis.estimated_key or ''} {analysis.estimated_scale or ''}".strip(),
                "rubato_index": analysis.expression.get("rubato_index"),
                "dynamic_range_db": analysis.expression.get("dynamic_range_db"),
                "spectral_centroid_mean": analysis.spectral.get("spectral_centroid_mean"),
                "transient_density_per_second": analysis.expression.get("transient_density_per_second"),
            }
        )
    return pd.DataFrame(rows).sort_values("piece_id").reset_index(drop=True) if rows else pd.DataFrame()


def analysis_by_piece_id(analyses: list[PieceAnalysis]) -> dict[str, PieceAnalysis]:
    return {analysis.piece_id: analysis for analysis in analyses}


def audio_by_piece_id(audio_analyses: list[AudioAnalysis]) -> dict[str, AudioAnalysis]:
    return {analysis.piece_id: analysis for analysis in audio_analyses}


def approximate_audio_times(
    measure_start: int,
    measure_end: int,
    measure_count: int,
    duration_seconds: float,
) -> tuple[float, float]:
    if measure_count <= 0:
        return (0.0, min(duration_seconds, 10.0))
    start_seconds = duration_seconds * max(0.0, float(measure_start - 1) / float(measure_count))
    end_seconds = duration_seconds * min(1.0, float(measure_end) / float(measure_count))
    if end_seconds <= start_seconds:
        end_seconds = min(duration_seconds, start_seconds + 8.0)
    return (round(start_seconds, 3), round(end_seconds, 3))


def audio_excerpt_widget(
    audio_path: Path | str,
    start_seconds: float,
    end_seconds: float,
    sample_rate: int = 22050,
):
    try:
        import librosa  # type: ignore
        from IPython.display import Audio
    except ImportError:
        return None

    duration = max(0.5, float(end_seconds) - float(start_seconds))
    clip, sr = librosa.load(str(audio_path), sr=sample_rate, mono=True, offset=float(start_seconds), duration=duration)
    if len(clip) == 0:
        return None
    return Audio(data=clip, rate=sr)


def approximate_region_audio_excerpt(
    analysis: PieceAnalysis,
    audio_analysis: AudioAnalysis,
    start_measure: int,
    end_measure: int,
):
    start_seconds, end_seconds = approximate_audio_times(
        measure_start=start_measure,
        measure_end=end_measure,
        measure_count=analysis.measure_count,
        duration_seconds=audio_analysis.duration_seconds,
    )
    return {
        "start_seconds": start_seconds,
        "end_seconds": end_seconds,
        "widget": audio_excerpt_widget(audio_analysis.source_path, start_seconds, end_seconds),
        "note": "Fragmento aproximado por proporcionalidad de compases, no alineacion exacta score-audio.",
    }


def _find_musescore_binary() -> str | None:
    candidates = [
        shutil.which("mscore"),
        shutil.which("MuseScore"),
        "/Applications/MuseScore Studio 4.app/Contents/MacOS/mscore",
        "/Applications/MuseScore 4.app/Contents/MacOS/mscore",
        "/Applications/MuseScore 3.app/Contents/MacOS/mscore",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def render_score_excerpt_image(
    score_path: Path | str,
    start_measure: int,
    end_measure: int,
    output_dir: Path | str,
) -> Path | None:
    musescore_bin = _find_musescore_binary()
    if musescore_bin is None:
        return None

    score = load_score(Path(score_path))
    excerpt = score.measures(start_measure, end_measure)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)
        xml_path = tmp_dir_path / "excerpt.musicxml"
        base_png_path = output_dir / f"{Path(score_path).stem}_mm_{start_measure}_{end_measure}.png"
        excerpt.write("musicxml", fp=str(xml_path))
        result = subprocess.run(
            [musescore_bin, str(xml_path), "-o", str(base_png_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        if base_png_path.exists():
            return base_png_path
        numbered_png = output_dir / f"{base_png_path.stem}-1.png"
        if numbered_png.exists():
            return numbered_png
    return None


def _load_librosa():
    import librosa  # type: ignore

    return librosa


def local_audio_similarity_table(
    audio_analyses: list[AudioAnalysis],
    window_seconds: float = 12.0,
    hop_seconds: float = 6.0,
    top_n: int = 10,
) -> pd.DataFrame:
    if len(audio_analyses) < 2:
        return pd.DataFrame()

    librosa = _load_librosa()
    windows: list[dict[str, object]] = []
    for analysis in audio_analyses:
        audio, sr = librosa.load(str(analysis.source_path), sr=22050, mono=True)
        if len(audio) == 0:
            continue
        win_length = max(1, int(window_seconds * sr))
        hop_length = max(1, int(hop_seconds * sr))
        for start in range(0, max(1, len(audio) - win_length + 1), hop_length):
            end = min(len(audio), start + win_length)
            clip = audio[start:end]
            if len(clip) < sr:
                continue
            chroma = librosa.feature.chroma_cens(y=clip, sr=sr)
            rms = librosa.feature.rms(y=clip)[0]
            centroid = librosa.feature.spectral_centroid(y=clip, sr=sr)[0]
            feature_vector = np.concatenate(
                [
                    np.mean(chroma, axis=1),
                    np.array(
                        [
                            float(np.mean(rms)),
                            float(np.std(rms)),
                            float(np.mean(centroid) / 5000.0),
                        ]
                    ),
                ]
            )
            windows.append(
                {
                    "piece_id": analysis.piece_id,
                    "title": _piece_title(analysis.piece_id, analysis.case_study_id),
                    "start_seconds": round(float(start) / float(sr), 3),
                    "end_seconds": round(float(end) / float(sr), 3),
                    "feature_vector": feature_vector,
                }
            )

    rows: list[dict[str, object]] = []
    for left_index in range(len(windows)):
        left = windows[left_index]
        left_vector = left["feature_vector"]
        left_norm = float(np.linalg.norm(left_vector))
        if left_norm <= 0.0:
            continue
        for right_index in range(left_index + 1, len(windows)):
            right = windows[right_index]
            if left["piece_id"] == right["piece_id"]:
                continue
            right_vector = right["feature_vector"]
            right_norm = float(np.linalg.norm(right_vector))
            if right_norm <= 0.0:
                continue
            similarity = float(np.dot(left_vector, right_vector) / (left_norm * right_norm))
            rows.append(
                {
                    "left_piece": left["piece_id"],
                    "left_title": left["title"],
                    "left_start_seconds": left["start_seconds"],
                    "left_end_seconds": left["end_seconds"],
                    "right_piece": right["piece_id"],
                    "right_title": right["title"],
                    "right_start_seconds": right["start_seconds"],
                    "right_end_seconds": right["end_seconds"],
                    "similarity": round(similarity, 4),
                }
            )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values("similarity", ascending=False).head(top_n).reset_index(drop=True)


def piece_overview_card(
    analysis: PieceAnalysis | None,
    audio_analysis: AudioAnalysis | None,
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
) -> pd.DataFrame:
    piece_id = analysis.piece_id if analysis is not None else audio_analysis.piece_id if audio_analysis is not None else "unknown"
    return pd.DataFrame(
        [
            {
                "piece_id": piece_id,
                "title": _piece_title(piece_id, case_study_id=case_study_id),
                "symbolic_source": analysis.corpus_profile_id if analysis is not None else "not available",
                "global_key_score": analysis.global_key if analysis is not None else "not available",
                "local_keys": len(analysis.key_regions) if analysis is not None else 0,
                "cadences": len(analysis.cadences) if analysis is not None else 0,
                "tempo_bpm_audio": audio_analysis.tempo_bpm if audio_analysis is not None else None,
                "estimated_key_audio": (
                    f"{audio_analysis.estimated_key or ''} {audio_analysis.estimated_scale or ''}".strip()
                    if audio_analysis is not None
                    else "not available"
                ),
                "rubato_index": audio_analysis.expression.get("rubato_index") if audio_analysis is not None else None,
            }
        ]
    )
