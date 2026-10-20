#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v brew >/dev/null || { echo 'Homebrew required for FFmpeg and FFprobe when building'; exit 1; }
command -v python3 >/dev/null || { echo 'Python 3.11+ required when building'; exit 1; }
command -v ffmpeg >/dev/null || brew install ffmpeg
command -v ffprobe >/dev/null || brew install ffmpeg
python3 -m pip install --disable-pip-version-check -r requirements-build.txt
python3 -m PyInstaller --noconfirm --clean --windowed --onedir \
  --name FileTidy \
  --add-binary "$(command -v ffmpeg):." \
  --add-binary "$(command -v ffprobe):." \
  --collect-all PIL \
  --hidden-import duplicate_engine \
  --hidden-import history_store \
  duplicate_finder.py
codesign --force --deep --sign - dist/FileTidy.app
# Keep the .app resource fork/permissions intact in a portable ZIP.
mkdir -p release
ditto -c -k --sequesterRsrc --keepParent dist/FileTidy.app release/FileTidy_macOS.zip
echo 'Done: release/FileTidy_macOS.zip'
