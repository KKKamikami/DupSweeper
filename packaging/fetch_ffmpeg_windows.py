"""Build-time Windows FFmpeg downloader. Checks publisher SHA-256 before extraction."""
import hashlib
import re
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

URL = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
MAX_SIZE = 350 * 1024 * 1024
DEST = Path(__file__).resolve().parents[1] / 'build-tools'


def main():
    DEST.mkdir(exist_ok=True)
    with urllib.request.urlopen(URL + '.sha256', timeout=40) as r:
        published = r.read(4096).decode('ascii', errors='replace')
    match = re.search(r'(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])', published)
    if match is None:
        raise RuntimeError('Source publisher did not return a SHA-256 checksum')
    expected = match.group().lower()
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / 'ffmpeg.zip'
        h = hashlib.sha256()
        size = 0
        with urllib.request.urlopen(URL, timeout=60) as response, archive.open('wb') as output:
            while block := response.read(1024 * 1024):
                size += len(block)
                if size > MAX_SIZE:
                    raise RuntimeError('Download exceeds maximum archive size')
                h.update(block)
                output.write(block)
        if h.hexdigest().lower() != expected:
            raise RuntimeError('Archive SHA-256 differs from publisher checksum')
        with zipfile.ZipFile(archive) as z:
            for exe in ('ffmpeg.exe', 'ffprobe.exe'):
                matches = [i for i in z.infolist() if
                           i.filename.replace('\\','/').endswith('/bin/' + exe)
                           and not i.is_dir()]
                if len(matches) != 1 or matches[0].file_size > 250 * 1024 * 1024:
                    raise RuntimeError('Unexpected ZIP contents for ' + exe)
                with z.open(matches[0]) as src, (DEST / exe).open('wb') as out:
                    shutil.copyfileobj(src, out)
    print('FFmpeg binaries verified and ready at', DEST)


if __name__ == '__main__':
    sys.exit(main())
