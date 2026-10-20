from pathlib import Path
import duplicate_engine as engine
import history_store as history


def test_storage_namespaces_independent():
    assert 'FileTidyFinal' in str(history.storage_path())
    assert 'FileTidyFinal' in str(engine.cache_file())
    assert 'DuplicateFinderV3' not in str(history.storage_path())
    assert 'DuplicateFinderV4' not in str(engine.cache_file())


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
