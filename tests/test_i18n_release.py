"""Regression tests for both languages and four release artifacts."""
from pathlib import Path
import tempfile
import zipfile
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dupsweeper_i18n import set_language,T

def test_english_controls():
    set_language('en')
    assert T('掃描位置')=='Scan locations'
    assert T('智慧選取相似影片（信任）')=='Trust Smart Select for similar videos'
    assert T('完整掃描歷史')=='Full Scan History'
    assert '中文' not in T('智慧選取')
    set_language('zh-TW')
    assert T('智慧選取')=='智慧選取'

def test_windows_english_build_entrypoint():
    root=Path(__file__).resolve().parents[1]
    script=(root/'packaging/build_windows.ps1').read_text()
    assert 'dupsweeper_en.py' in script
    assert "'DupSweeper_en'" in script
    assert (root/'dupsweeper_en.py').is_file()

def test_four_release_names_and_embedded_macos_archives():
    from importlib.util import spec_from_file_location,module_from_spec
    root=Path(__file__).resolve().parents[1]
    spec=spec_from_file_location('dupsweeper_assemble',root/'packaging/assemble_release.py')
    module=module_from_spec(spec);spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory() as d:
        base=Path(d)
        for sub,filename in [('windows','DupSweeper_zh-TW.exe'),('windows','DupSweeper_en.exe'),('ubuntu','DupSweeper_Ubuntu_all_v1.2.0.deb')]:
            p=base/'inputs'/sub/filename;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fake payload' * 20)
        for arch in ('mac_arm','mac_intel'):
            p=base/'inputs'/arch/'DupSweeper_macOS.zip';p.parent.mkdir(parents=True,exist_ok=True)
            with zipfile.ZipFile(p,'w') as archive:archive.writestr('DupSweeper.app/Contents/MacOS/DupSweeper',b'sample')
        paths=module.build(base/'inputs',base/'out','1.2.0')
        assert len(paths)==4
        assert all(p.is_file() for p in paths)
        assert any(p.name=='DupSweeper_Windows_x64_en_v1.2.0.exe' for p in paths)
        with zipfile.ZipFile(base/'out'/'DupSweeper_macOS_v1.2.0.zip') as z:
            assert 'AppleSilicon/DupSweeper.app.zip' in z.namelist()
            assert 'Intel/DupSweeper.app.zip' in z.namelist()
