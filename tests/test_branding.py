from pathlib import Path
import dupsweeper_engine as engine
import dupsweeper_history as history

ROOT = Path(__file__).resolve().parents[1]

def test_application_brand_and_release_names():
    gui = (ROOT / 'dupsweeper.py').read_text(encoding='utf-8')
    assert "root.title(T('DupSweeper" in gui
    assert "text='DupSweeper'" in gui
    for name in ('packaging/build_windows.ps1', 'packaging/build_macos.sh',
                 'packaging/build_ubuntu.sh', 'packaging/assemble_release.py',
                 '.github/workflows/build-native.yml', 'README.md'):
        assert 'DupSweeper' in (ROOT / name).read_text(encoding='utf-8')

def test_independent_dupsweeper_data_folder():
    assert 'DupSweeper' in str(engine.cache_file())
    assert 'DupSweeper' in str(history.storage_path())

def test_new_entrypoints_and_builds():
    assert (ROOT / 'dupsweeper.py').is_file()
    assert (ROOT / 'dupsweeper_engine.py').is_file()
    assert (ROOT / 'dupsweeper_history.py').is_file()
    for suffix in ('ps1', 'sh'):
        assert (ROOT / ('packaging/build_windows.ps1' if suffix=='ps1' else 'packaging/build_macos.sh')).is_file()
    workflow=(ROOT / '.github/workflows/build-native.yml').read_text()
    assert 'run: bash packaging/build_macos.sh' in workflow
    assert 'macos-15-intel' in workflow
    assert 'macos-15' in workflow
