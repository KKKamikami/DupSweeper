# Windows security and SmartScreen

A GitHub Actions build passing its checks does **not** establish SmartScreen reputation. This project cannot programmatically suppress SmartScreen on another computer.

## Recommended distribution choices

1. **Microsoft Store**: For the strongest approach to avoiding SmartScreen download warnings, publish an approved MSIX app through Microsoft Store. Microsoft performs the signing for Store-submitted MSIX packages. Partner Center registration, identity verification, MSIX packaging and certification are required. The current GitHub release builds standalone EXE files, not a Store-submitted MSIX; a Store release must be prepared separately.
2. **Outside the Store (GitHub Releases)**: Obtain a valid trusted publisher signing identity (such as Microsoft Artifact Signing, formerly Trusted Signing, or a CA-issued OV certificate). Sign **both** Windows executables after building, with SHA-256 timestamping, and verify the Authenticode signature before distribution. Building a new EXE changes its file hash, and even signed files may warn until they develop positive reputation.
3. **Do not** remove the Mark-of-the-Web, tamper with Defender, add broad AV exclusions, ask users to disable SmartScreen, or pretend a self-signed certificate removes reputation warnings.

## GitHub Actions signing configuration

`packaging/sign_windows.ps1` already supports optional signing using a CA-trusted PFX certificate. Add both secrets in the GitHub repository's **Settings → Secrets and variables → Actions**:

- `WINDOWS_SIGN_PFX_BASE64`: base64 of the PFX certificate file containing the private signing key.
- `WINDOWS_SIGN_PFX_PASSWORD`: password for the PFX file.

Keep private keys OUT of the public repository. The workflow leaves binaries unsigned and reports a warning if credentials are absent. The current script supports an exportable PFX; providers using a cloud-HSM / Artifact Signing require their dedicated GitHub Actions signing integration instead. Always review the certificate provider's terms and identity requirements.

For every release, verify the signature of the downloaded final EXE using Windows PowerShell:

```powershell
Get-AuthenticodeSignature .\DupSweeper_Windows_x64_en_v1.3.0.exe | Format-List
```

`Status` should be `Valid` for a trusted signing certificate; check publisher details and the timestamp. `NotSigned` or `UnknownError` means do not claim the executable is signed.

## References

- https://learn.microsoft.com/windows/apps/package-and-deploy/smartscreen-reputation
- https://learn.microsoft.com/windows/apps/package-and-deploy/code-signing-options
