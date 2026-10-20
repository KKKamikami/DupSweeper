$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
$Root = (Get-Location).Path
Write-Host 'Building stand-alone Windows executable...'
python -m pip install --disable-pip-version-check -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Install build dependencies failed' }
python packaging/fetch_ffmpeg_windows.py
if ($LASTEXITCODE -ne 0) { throw 'FFmpeg download or verification failed' }
python -m PyInstaller --noconfirm --clean --onefile --windowed `
  --name FileTidy `
  --add-binary 'build-tools/ffmpeg.exe;.' `
  --add-binary 'build-tools/ffprobe.exe;.' `
  --collect-all PIL `
  --hidden-import duplicate_engine `
  --hidden-import history_store `
  duplicate_finder.py
if ($LASTEXITCODE -ne 0) { throw 'Windows executable build failed' }
if (-not (Test-Path 'dist/FileTidy.exe')) { throw 'Windows executable not found' }
Write-Host 'Done: dist/FileTidy.exe'
