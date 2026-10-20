$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
Write-Host 'Building Windows DupSweeper in Traditional Chinese and English...'
python -m pip install --disable-pip-version-check -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Build dependencies failed' }
python packaging/fetch_ffmpeg_windows.py
if ($LASTEXITCODE -ne 0) { throw 'FFmpeg verification failed' }
foreach ($flavor in @(@('DupSweeper_zh-TW','dupsweeper.py'), @('DupSweeper_en','dupsweeper_en.py'))) {
    $name = $flavor[0]; $entry = $flavor[1]
    python -m PyInstaller --noconfirm --clean --onefile --windowed `
      --name $name `
      --icon assets/dupsweeper.ico `
      --add-binary 'build-tools/ffmpeg.exe;.' `
      --add-binary 'build-tools/ffprobe.exe;.' `
      --collect-all PIL `
      --hidden-import dupsweeper `
      --hidden-import dupsweeper_i18n `
      --hidden-import dupsweeper_engine `
      --hidden-import dupsweeper_history `
      $entry
    if ($LASTEXITCODE -ne 0) { throw "Windows $name build failed" }
    if (-not (Test-Path "dist/$name.exe")) { throw "$name.exe was not generated" }
}
Write-Host 'Windows Chinese and English binaries created.'
