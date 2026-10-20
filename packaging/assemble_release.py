#!/usr/bin/env python3
"""Collect successful native GitHub Actions builds into four Release assets.

Usage:
  python packaging/assemble_release.py --inputs downloads --output release-assets
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import zipfile


def build(inputs: Path, output: Path, version: str) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    windows = inputs / 'windows' / 'DupSweeper_zh-TW.exe'
    english = inputs / 'windows' / 'DupSweeper_en.exe'
    arm = inputs / 'mac_arm' / 'DupSweeper_macOS.zip'
    intel = inputs / 'mac_intel' / 'DupSweeper_macOS.zip'
    ubuntu = inputs / 'ubuntu' / f'DupSweeper_Ubuntu_all_v{version}.deb'
    for path in (windows, english, arm, intel, ubuntu):
        if not path.is_file() or path.stat().st_size < 100:
            raise RuntimeError(f'Missing or unexpectedly small compiled asset: {path}')
    for path in (arm, intel):
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None or not any(n.endswith('Contents/MacOS/DupSweeper') for n in z.namelist()):
                raise RuntimeError(f'Invalid macOS application archive: {path}')
    result_windows = output / f'DupSweeper_Windows_x64_zh-TW_v{version}.exe'
    result_english = output / f'DupSweeper_Windows_x64_en_v{version}.exe'
    result_ubuntu = output / f'DupSweeper_Ubuntu_v{version}.deb'
    result_mac = output / f'DupSweeper_macOS_v{version}.zip'
    shutil.copyfile(windows, result_windows)
    shutil.copyfile(english, result_english)
    shutil.copyfile(ubuntu, result_ubuntu)
    with zipfile.ZipFile(result_mac, 'w', compression=zipfile.ZIP_STORED) as z:
        z.write(arm, 'AppleSilicon/DupSweeper.app.zip')
        z.write(intel, 'Intel/DupSweeper.app.zip')
        z.writestr('README.md',
                   '# macOS DupSweeper v' + version + '\n'
                   'M1/M2/M3/M4/M5 等 Apple 晶片：解壓 AppleSilicon/DupSweeper.app.zip。\n'
                   'Intel Mac：解壓 Intel/DupSweeper.app.zip。\n'
                   '在 Finder 雙擊 DupSweeper.app。尚未 Apple 公證，可能需要從「隱私權與安全性」允許。\n'
                   '影像與影片分析完全在本機執行。\n')
    return [result_windows, result_english, result_mac, result_ubuntu]


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--inputs', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    version = (Path(__file__).resolve().parents[1] / 'VERSION').read_text().strip()
    for p in build(args.inputs, args.output, version):
        print(f'RELEASE_ASSET: {p} ({p.stat().st_size} bytes)')
