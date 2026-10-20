from pathlib import Path
import dupsweeper_engine as engine
import dupsweeper_history as history


def test_storage_namespaces_independent():
    assert 'DupSweeper' in str(history.storage_path())
    assert 'DupSweeper' in str(engine.cache_file())


def test_only_markdown_readme():
    root=Path(__file__).resolve().parents[1]
    assert (root/'README.md').exists()
    assert not list(root.glob('README*.txt'))


def test_native_build_scripts_present():
    root=Path(__file__).resolve().parents[1]
    for item in ('packaging/build_windows.ps1','packaging/build_macos.sh',
                 '.github/workflows/build-native.yml'):
        assert (root/item).is_file()
    assert '--onefile' in (root/'packaging/build_windows.ps1').read_text()
    assert '--windowed' in (root/'packaging/build_macos.sh').read_text()
