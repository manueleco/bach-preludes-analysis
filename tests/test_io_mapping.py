from pathlib import Path

from bach_preludes_analysis.io import infer_piece_id


def test_infer_piece_id_normalizes_kern_style_name():
    assert infer_piece_id(Path("bwv1007-01.krn")) == "suite_01_prelude_g_major_bwv1007"


def test_infer_piece_id_normalizes_verbose_editorial_name():
    input_path = Path("Cello Suite no. 4 Prelude - BWV 1010.xml")

    assert infer_piece_id(input_path) == "suite_04_prelude_eb_major_bwv1010"
