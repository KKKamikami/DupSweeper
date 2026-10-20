#!/usr/bin/env bash
# Build an installable Ubuntu .deb; no Python packaging or compiling is needed by end users.
set -euo pipefail
cd "$(dirname "$0")/.."
VERSION="$(tr -d '\r\n' < VERSION)"
OUT="$(pwd)/release"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/DEBIAN" "$STAGE/usr/bin" "$STAGE/usr/share/dupsweeper" \
         "$STAGE/usr/share/applications" "$STAGE/usr/share/doc/dupsweeper" \
         "$STAGE/usr/share/icons/hicolor/256x256/apps" "$OUT"
cat > "$STAGE/DEBIAN/control" <<CONTROL
Package: dupsweeper
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Maintainer: DupSweeper Contributors <noreply@example.invalid>
Depends: python3 (>= 3.10), python3-tk, python3-pil, python3-send2trash, ffmpeg
Description: Local duplicate-file organizer and visual similarity checker
 DupSweeper compares exact duplicates and similar photos/videos locally,
 offers priority folders and safe selection, and moves reviewed files to Trash.
CONTROL
install -m 0644 dupsweeper_engine.py dupsweeper.py dupsweeper_history.py "$STAGE/usr/share/dupsweeper/"
install -m 0644 README.md "$STAGE/usr/share/doc/dupsweeper/README.md"
install -m 0644 assets/dupsweeper.png "$STAGE/usr/share/icons/hicolor/256x256/apps/dupsweeper.png"
cat > "$STAGE/usr/bin/dupsweeper" <<'LAUNCH'
#!/bin/sh
exec /usr/bin/python3 /usr/share/dupsweeper/dupsweeper.py "$@"
LAUNCH
chmod 0755 "$STAGE/usr/bin/dupsweeper"
cat > "$STAGE/usr/share/applications/dupsweeper.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=DupSweeper
Comment=本機重複檔案搜尋與相似媒體比對
Exec=dupsweeper
Icon=dupsweeper
Terminal=false
Categories=Utility;FileTools;
StartupNotify=true
DESKTOP
OUTPUT="$OUT/DupSweeper_Ubuntu_all_v${VERSION}.deb"
dpkg-deb --build --root-owner-group "$STAGE" "$OUTPUT"
dpkg-deb --info "$OUTPUT" >/dev/null
printf 'OK: %s\n' "$OUTPUT"
