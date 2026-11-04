from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bach_preludes_analysis.config import DATA_CASE_STUDIES_DIR, DEFAULT_CASE_STUDY_ID


@dataclass(frozen=True)
class CaseStudy:
    case_study_id: str
    label: str
    composer: str
    collection_title: str
    description: str
    root_dir: Path
    catalog_path: Path
    symbolic_curated_dir: Path
    symbolic_raw_pdf_dir: Path
    symbolic_manifest_dir: Path
    symbolic_converted_audiveris_dir: Path
    audio_private_reference_dir: Path
    audio_inbox_dir: Path
    audio_processed_dir: Path


def _build_bach_cello_suites_case_study() -> CaseStudy:
    root_dir = DATA_CASE_STUDIES_DIR / "bach_cello_suites"
    return CaseStudy(
        case_study_id="bach_cello_suites",
        label="Bach cello suite preludes",
        composer="Johann Sebastian Bach",
        collection_title="Six Cello Suites, preludes only",
        description=(
            "Caso de estudio base del repo: los preludios de las Suites para violonchelo solo "
            "BWV 1007-1012, con armonia simbolica curada y audio privado para expresion."
        ),
        root_dir=root_dir,
        catalog_path=root_dir / "catalog" / "pieces.csv",
        symbolic_curated_dir=root_dir / "symbolic" / "official_curated",
        symbolic_raw_pdf_dir=root_dir / "symbolic" / "raw_pdfs",
        symbolic_manifest_dir=root_dir / "symbolic" / "manifests",
        symbolic_converted_audiveris_dir=root_dir / "symbolic" / "converted" / "audiveris",
        audio_private_reference_dir=root_dir / "audio" / "private_reference",
        audio_inbox_dir=root_dir / "audio" / "inbox",
        audio_processed_dir=root_dir / "audio" / "processed",
    )


CASE_STUDIES: dict[str, CaseStudy] = {
    "bach_cello_suites": _build_bach_cello_suites_case_study(),
}


def get_case_study(case_study_id: str = DEFAULT_CASE_STUDY_ID) -> CaseStudy:
    try:
        return CASE_STUDIES[case_study_id]
    except KeyError as exc:
        available = ", ".join(sorted(CASE_STUDIES))
        raise ValueError(f"Unknown case study '{case_study_id}'. Available case studies: {available}.") from exc


def list_case_studies() -> list[CaseStudy]:
    return sorted(CASE_STUDIES.values(), key=lambda study: study.case_study_id)


def build_case_study_rows() -> list[dict[str, str]]:
    return [
        {
            "case_study_id": study.case_study_id,
            "label": study.label,
            "composer": study.composer,
            "collection": study.collection_title,
            "root_dir": str(study.root_dir),
            "description": study.description,
        }
        for study in list_case_studies()
    ]
