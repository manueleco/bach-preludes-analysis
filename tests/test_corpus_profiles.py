from bach_preludes_analysis.config import DATA_RAW_DIR
from bach_preludes_analysis.corpus_profiles import ANALYSIS_POLICY, build_profile_rows, get_profile, resolve_symbolic_input_dir


def test_official_curated_profile_points_to_raw_dir():
    profile = get_profile("official_curated")

    assert profile.domain == "symbolic"
    assert profile.root_dir == DATA_RAW_DIR
    assert profile.reliability["roman_numerals"] == "high"


def test_profile_rows_include_requested_profiles():
    profile_ids = {row["profile_id"] for row in build_profile_rows("symbolic")}

    assert {"official_curated", "kern_reference", "mutopia_reference", "musopen_reference"} <= profile_ids
    assert ANALYSIS_POLICY


def test_symbolic_input_dir_defaults_to_profile_root():
    assert resolve_symbolic_input_dir("official_curated", explicit_input_dir=None) == DATA_RAW_DIR
