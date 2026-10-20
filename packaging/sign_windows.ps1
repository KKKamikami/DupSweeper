$ErrorActionPreference='Stop'
if ([string]::IsNullOrWhiteSpace($env:WINDOWS_SIGN_PFX_BASE64) -or [string]::IsNullOrWhiteSpace($env:WINDOWS_SIGN_PFX_PASSWORD)) {
    Write-Host 'Code signing skipped: certificate secrets are not configured. SmartScreen may warn on unsigned downloads.'
    exit 0
}
$cert = Join-Path $env:RUNNER_TEMP 'dupsweeper_signing.pfx'
try {
    [IO.File]::WriteAllBytes($cert,[Convert]::FromBase64String($env:WINDOWS_SIGN_PFX_BASE64))
    $command = Get-Command 'signtool.exe' -ErrorAction SilentlyContinue
    $signtool = if ($command) { $command.Source } else { $null }
    if (-not $signtool) {
        $kits = Join-Path ${env:ProgramFiles(x86)} 'Windows Kits/10/bin'
        $candidate = Get-ChildItem -Path $kits -Filter signtool.exe -Recurse -ErrorAction SilentlyContinue |
                     Where-Object { $_.FullName -match '[\\/]x64[\\/]signtool\.exe$' } |
                     Sort-Object FullName -Descending | Select-Object -First 1
        if ($candidate) { $signtool = $candidate.FullName }
    }
    if (-not $signtool) { throw 'signtool.exe is unavailable; install Windows SDK.' }
    foreach ($filename in @('DupSweeper_zh-TW.exe','DupSweeper_en.exe')) {
        & $signtool sign /f $cert /p $env:WINDOWS_SIGN_PFX_PASSWORD /fd SHA256 /td SHA256 /tr 'http://timestamp.digicert.com' (Join-Path (Resolve-Path './dist') $filename)
        if ($LASTEXITCODE -ne 0) { throw "Code signing failed: $filename" }
        & $signtool verify /pa /v (Join-Path (Resolve-Path './dist') $filename)
        if ($LASTEXITCODE -ne 0) { throw "Signature validation failed: $filename" }
    }
} finally {
    if (Test-Path $cert) { Remove-Item -Force $cert }
}
