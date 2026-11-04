import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from music21 import converter, note, stream

from bach_preludes_analysis.analysis.audio_essentia import _framewise_features
from bach_preludes_analysis.config import PROJECT_ROOT
from bach_preludes_analysis.io import infer_piece_id


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mxl_is_converted_to_real_musicxml(tmp_path):
    prepare = load_script('prepare_case_study_corpus')
    score = stream.Score()
    part = stream.Part()
    part.append(note.Note('G3', quarterLength=4))
    score.insert(0, part)
    source = Path(score.write('mxl', fp=tmp_path / 'bwv1007_prelude.mxl'))
    assert source.read_bytes().startswith(b'PK')

    output = tmp_path / 'curated'
    prepare._prepare_single_score(source, output, 'bach_cello_suites', False)

    target = output / 'suite_01_prelude_g_major_bwv1007.musicxml'
    assert target.read_bytes().lstrip().startswith(b'<?xml')
    assert len(converter.parse(target).recurse().notes) == 1


@pytest.mark.parametrize('mode', ['copy', 'move'])
def test_audio_transfer_preserves_existing_recording(tmp_path, mode):
    organizer = load_script('organize_case_study_audio')
    source, target = tmp_path / 'new.wav', tmp_path / 'reference.wav'
    source.write_bytes(b'new recording')
    target.write_bytes(b'existing recording')

    with pytest.raises(FileExistsError):
        organizer._transfer(source, target, mode, False)

    assert source.read_bytes() == b'new recording'
    assert target.read_bytes() == b'existing recording'


def test_audio_organizer_skips_unknown_piece(tmp_path, monkeypatch):
    organizer = load_script('organize_case_study_audio')
    inbox = tmp_path / 'inbox'
    inbox.mkdir()
    (inbox / 'unrelated_recording.wav').write_bytes(b'local audio')
    output = tmp_path / 'organized'
    monkeypatch.setattr(organizer, '_parse_args', lambda: SimpleNamespace(
        input_dir=str(inbox), output_dir=str(output), case_study='bach_cello_suites',
        mode='copy', dry_run=False,
    ))
    organizer.main()
    assert not output.exists()


def test_catalog_does_not_match_partial_work_numbers():
    assert infer_piece_id(Path('bwv10070_prelude.xml')) == 'bwv10070_prelude'


def test_essentia_features_use_bandwidth_and_single_input_flux():
    spectra = [np.array([0., 1., 0.]), np.ones(3)]
    flux_inputs = []

    def flux(spectrum):
        flux_inputs.append(spectrum)
        return 2.0

    es = SimpleNamespace(
        Windowing=lambda **kwargs: lambda frame: frame,
        Spectrum=lambda: lambda frame: frame,
        RMS=lambda: lambda frame: np.sqrt(np.mean(frame ** 2)),
        Centroid=lambda **kwargs: lambda frame: 2000.,
        Flux=lambda: flux,
        FrameGenerator=lambda *args, **kwargs: iter(spectra),
    )
    result = _framewise_features(es, np.ones(8), 8000, 4, 2)
    # A single bin has zero bandwidth; three equal bins span 0, 2 and 4 kHz.
    assert result['spectral_bandwidth_mean'] == pytest.approx(np.sqrt(8_000_000 / 3) / 2)
    assert result['spectral_flatness_mean'] == pytest.approx(0.5, abs=1e-5)
    assert len(flux_inputs) == 2
    np.testing.assert_array_equal(result['spectral_flux_values'], [0., 2.])
