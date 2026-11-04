from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from bach_preludes_analysis.case_studies import get_case_study
from bach_preludes_analysis.config import (
    DATA_SOURCES_SYMBOLIC_KERN_DIR,
    DATA_SOURCES_SYMBOLIC_MUSOPEN_DIR,
    DATA_SOURCES_SYMBOLIC_MUTOPIA_DIR,
    DEFAULT_CASE_STUDY_ID,
)

RELIABILITY_LABELS = {
    "high": "alta",
    "medium": "media",
    "review": "requiere revision musical",
    "low": "baja",
    "not_recommended": "no recomendable",
}

ANALYSIS_POLICY = [
    "Para armonia simbolica, usa el corpus curado del caso de estudio como fuente principal de verdad.",
    "Los corpus externos sirven para contraste editorial y computacional, no para reemplazar el score curado.",
    "Para audio comparativo, usa un solo interprete y una sola edicion o album por caso de estudio.",
    "Usa el audio para expresion, timing y sonoridad; usa el score curado para armonia, funcion y cadencias.",
]


@dataclass(frozen=True)
class CorpusProfile:
    profile_id: str
    label: str
    domain: str
    source_family: str
    description: str
    role: str
    primary_formats: tuple[str, ...]
    reliability: dict[str, str]
    root_dir: Path | None = None
    case_study_root_attr: str | None = None
    reference_url: str | None = None


PROFILE_TEMPLATES: dict[str, CorpusProfile] = {
    "official_curated": CorpusProfile(
        profile_id="official_curated",
        label="Official curated symbolic corpus",
        domain="symbolic",
        case_study_root_attr="symbolic_curated_dir",
        source_family="curated_musicxml",
        description="Corpus simbolico principal, curado a mano y listo para analisis armonico serio.",
        role="Fuente principal para armonia, tonalidad, funcion, cadencias y comparacion estructural.",
        primary_formats=("MusicXML", "MXL", "XML", "MIDI"),
        reliability={
            "global_tonality": "high",
            "local_tonality": "high",
            "chords_and_inversions": "high",
            "roman_numerals": "high",
            "tonicizations_and_modulations": "high",
            "cadences": "review",
            "non_chord_tones": "review",
            "sequences": "high",
            "chromaticism": "high",
            "voice_leading": "review",
            "expression": "not_recommended",
        },
    ),
    "kern_reference": CorpusProfile(
        profile_id="kern_reference",
        label="Humdrum / kern reference corpus",
        domain="symbolic",
        root_dir=DATA_SOURCES_SYMBOLIC_KERN_DIR,
        source_family="humdrum_kern",
        description="Referencia simbolica en formato **kern, util para trazabilidad computacional y contraste.",
        role="Corpus externo para comparar lecturas estructurales y revisar discrepancias de segmentacion.",
        primary_formats=("Kern",),
        reliability={
            "global_tonality": "medium",
            "local_tonality": "medium",
            "chords_and_inversions": "medium",
            "roman_numerals": "medium",
            "tonicizations_and_modulations": "medium",
            "cadences": "review",
            "non_chord_tones": "low",
            "sequences": "medium",
            "chromaticism": "medium",
            "voice_leading": "review",
            "expression": "not_recommended",
        },
        reference_url="https://github.com/humdrum-tools/humdrum-data",
    ),
    "mutopia_reference": CorpusProfile(
        profile_id="mutopia_reference",
        label="Mutopia symbolic reference corpus",
        domain="symbolic",
        root_dir=DATA_SOURCES_SYMBOLIC_MUTOPIA_DIR,
        source_family="mutopia_lilypond",
        description="Referencia simbolica exportada desde Mutopia, util para contraste editorial y estructura.",
        role="Contraste simbolico de una edicion abierta; no sustituye el corpus curado.",
        primary_formats=("MIDI", "PDF", "LilyPond export"),
        reliability={
            "global_tonality": "medium",
            "local_tonality": "medium",
            "chords_and_inversions": "medium",
            "roman_numerals": "medium",
            "tonicizations_and_modulations": "medium",
            "cadences": "review",
            "non_chord_tones": "low",
            "sequences": "medium",
            "chromaticism": "medium",
            "voice_leading": "review",
            "expression": "not_recommended",
        },
        reference_url="https://www.mutopiaproject.org/",
    ),
    "musopen_reference": CorpusProfile(
        profile_id="musopen_reference",
        label="Musopen reference corpus",
        domain="symbolic",
        root_dir=DATA_SOURCES_SYMBOLIC_MUSOPEN_DIR,
        source_family="musopen_score",
        description="Referencia abierta desde Musopen; valida para contraste de material, no como edicion definitiva.",
        role="Usala para cubrir huecos o revisar variantes, especialmente cuando falten otras transcripciones abiertas.",
        primary_formats=("PDF", "MIDI", "MusicXML export if available"),
        reliability={
            "global_tonality": "medium",
            "local_tonality": "medium",
            "chords_and_inversions": "review",
            "roman_numerals": "review",
            "tonicizations_and_modulations": "review",
            "cadences": "low",
            "non_chord_tones": "low",
            "sequences": "medium",
            "chromaticism": "medium",
            "voice_leading": "low",
            "expression": "not_recommended",
        },
        reference_url="https://musopen.org/",
    ),
    "audiveris_intermediate": CorpusProfile(
        profile_id="audiveris_intermediate",
        label="Audiveris intermediate OMR staging",
        domain="symbolic",
        case_study_root_attr="symbolic_converted_audiveris_dir",
        source_family="omr_staging",
        description="Staging intermedio de OMR. Solo sirve como paso previo a la curacion musical.",
        role="Fallback temporal cuando aun no existe un corpus curado suficiente.",
        primary_formats=("MXL", "MusicXML"),
        reliability={
            "global_tonality": "review",
            "local_tonality": "low",
            "chords_and_inversions": "low",
            "roman_numerals": "low",
            "tonicizations_and_modulations": "low",
            "cadences": "low",
            "non_chord_tones": "low",
            "sequences": "review",
            "chromaticism": "low",
            "voice_leading": "low",
            "expression": "not_recommended",
        },
    ),
    "single_interpreter_reference": CorpusProfile(
        profile_id="single_interpreter_reference",
        label="Single-interpreter private reference recordings",
        domain="audio",
        case_study_root_attr="audio_private_reference_dir",
        source_family="single_album_audio",
        description=(
            "Grabaciones privadas y locales de un solo interprete y una sola edicion o album "
            "para comparabilidad expresiva seria. No se publican en GitHub."
        ),
        role="Fuente principal para tempo local, rubato, dinamica, densidad espectral y articulacion.",
        primary_formats=("WAV", "FLAC", "AIFF", "MP3"),
        reliability={
            "tempo_local": "high",
            "rubato": "high",
            "dynamics": "medium",
            "spectral_density": "medium",
            "articulation": "review",
            "key_from_audio": "medium",
            "harmony": "not_recommended",
            "roman_numerals": "not_recommended",
            "cadences": "not_recommended",
            "comparability": "high",
        },
    ),
    "raw_audio_misc": CorpusProfile(
        profile_id="raw_audio_misc",
        label="Exploratory audio inbox",
        domain="audio",
        case_study_root_attr="audio_inbox_dir",
        source_family="mixed_audio",
        description="Carpeta de ingreso para audio local y privado. Util para pruebas antes de curar el corpus interpretativo.",
        role="Sandbox de audio antes de normalizar nombres y mover archivos al corpus comparativo principal.",
        primary_formats=("WAV", "FLAC", "AIFF", "MP3"),
        reliability={
            "tempo_local": "medium",
            "rubato": "medium",
            "dynamics": "low",
            "spectral_density": "low",
            "articulation": "low",
            "key_from_audio": "medium",
            "harmony": "not_recommended",
            "roman_numerals": "not_recommended",
            "cadences": "not_recommended",
            "comparability": "low",
        },
    ),
}


def _materialize_profile(profile: CorpusProfile, case_study_id: str = DEFAULT_CASE_STUDY_ID) -> CorpusProfile:
    if profile.root_dir is not None:
        return profile
    if profile.case_study_root_attr is None:
        raise ValueError(f"Profile '{profile.profile_id}' does not define a root directory.")
    case_study = get_case_study(case_study_id)
    return replace(profile, root_dir=getattr(case_study, profile.case_study_root_attr))


def get_profile(profile_id: str, case_study_id: str = DEFAULT_CASE_STUDY_ID) -> CorpusProfile:
    try:
        template = PROFILE_TEMPLATES[profile_id]
    except KeyError as exc:
        available = ", ".join(sorted(PROFILE_TEMPLATES))
        raise ValueError(f"Unknown corpus profile '{profile_id}'. Available profiles: {available}.") from exc
    return _materialize_profile(template, case_study_id=case_study_id)


def list_profiles(domain: str | None = None, case_study_id: str = DEFAULT_CASE_STUDY_ID) -> list[CorpusProfile]:
    profiles = (get_profile(profile_id, case_study_id=case_study_id) for profile_id in PROFILE_TEMPLATES)
    if domain is not None:
        profiles = (profile for profile in profiles if profile.domain == domain)
    return sorted(profiles, key=lambda profile: profile.profile_id)


def build_profile_rows(domain: str | None = None, case_study_id: str = DEFAULT_CASE_STUDY_ID) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for profile in list_profiles(domain, case_study_id=case_study_id):
        reliability_summary = ", ".join(
            f"{metric}: {RELIABILITY_LABELS.get(level, level)}"
            for metric, level in list(profile.reliability.items())[:4]
        )
        rows.append(
            {
                "profile_id": profile.profile_id,
                "label": profile.label,
                "domain": profile.domain,
                "root_dir": str(profile.root_dir),
                "role": profile.role,
                "formats": ", ".join(profile.primary_formats),
                "reliability_preview": reliability_summary,
            }
        )
    return rows


def build_reliability_rows(profile_id: str, case_study_id: str = DEFAULT_CASE_STUDY_ID) -> list[dict[str, str]]:
    profile = get_profile(profile_id, case_study_id=case_study_id)
    return [
        {
            "profile_id": profile.profile_id,
            "metric": metric,
            "level": RELIABILITY_LABELS.get(level, level),
        }
        for metric, level in profile.reliability.items()
    ]


def resolve_symbolic_input_dir(
    profile_id: str = "official_curated",
    explicit_input_dir: Path | None = None,
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
) -> Path:
    if explicit_input_dir is not None:
        return explicit_input_dir
    profile = get_profile(profile_id, case_study_id=case_study_id)
    if profile.domain != "symbolic":
        raise ValueError(f"Profile '{profile_id}' is not a symbolic corpus profile.")
    return profile.root_dir


def resolve_audio_input_dir(
    profile_id: str = "single_interpreter_reference",
    explicit_input_dir: Path | None = None,
    case_study_id: str = DEFAULT_CASE_STUDY_ID,
) -> Path:
    if explicit_input_dir is not None:
        return explicit_input_dir
    profile = get_profile(profile_id, case_study_id=case_study_id)
    if profile.domain != "audio":
        raise ValueError(f"Profile '{profile_id}' is not an audio corpus profile.")
    return profile.root_dir


def available_paths_for_profile(profile_id: str, case_study_id: str = DEFAULT_CASE_STUDY_ID) -> list[Path]:
    profile = get_profile(profile_id, case_study_id=case_study_id)
    if not profile.root_dir.exists():
        return []

    if profile.domain == "symbolic":
        from bach_preludes_analysis.io import discover_score_paths

        return discover_score_paths(profile.root_dir)

    from bach_preludes_analysis.io import discover_audio_paths

    return discover_audio_paths(profile.root_dir)


def build_availability_rows(domain: str | None = None, case_study_id: str = DEFAULT_CASE_STUDY_ID) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for profile in list_profiles(domain, case_study_id=case_study_id):
        rows.append(
            {
                "profile_id": profile.profile_id,
                "label": profile.label,
                "file_count": len(available_paths_for_profile(profile.profile_id, case_study_id=case_study_id)),
                "root_dir": str(profile.root_dir),
            }
        )
    return rows
