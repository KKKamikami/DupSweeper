# Windows distribution and SmartScreen

DupSweeper does not disable Microsoft Defender, SmartScreen or Windows security policy. An application cannot reliably suppress SmartScreen before it is launched.

## For a reliably warning-free consumer installation

Publish a Microsoft Store-certified **packaged MSIX application** through Microsoft Partner Center. The Store signs and distributes certified MSIX packages. Store-installed applications do not display SmartScreen download reputation warnings. This requires a developer account, a packaged and tested MSIX, and Microsoft's certification process. **The GitHub Actions build currently produces standalone EXE files, not a Microsoft Store submission.**

- SmartScreen reputation (Microsoft): https://learn.microsoft.com/windows/apps/package-and-deploy/smartscreen-reputation
- MSIX / Store publishing: https://learn.microsoft.com/windows/apps/distribute-through-store/how-to-distribute-your-win32-app-through-microsoft-store

Publishing an unpackaged Win32 EXE through the Store is a different path; it requires a properly signed installer and is not the same as Store-signed packaged MSIX distribution. Do not claim Store certification until approved.

## For GitHub Releases

Use a trusted Authenticode publisher signing identity (Microsoft Artifact Signing where eligible, or a trusted CA-issued code-signing certificate). Sign both Windows EXEs with SHA-256 and a timestamp, verify signatures, and never modify the signed binaries. **No signing certificate (including EV) guarantees immediate SmartScreen reputation.** Reputation depends on publisher identity and downloaded-file reputation.

The supplied workflow supports `WINDOWS_SIGN_PFX_BASE64` and `WINDOWS_SIGN_PFX_PASSWORD` repository Actions secrets for certificates supporting an exportable PFX. Never upload your private signing key to a public repo. Hardware-backed/cloud signing identities need a separate provider-specific integration.

For a production release, choose **Require trusted Windows signature** in the workflow dispatch form to fail the run when either EXE has no valid Authenticode signature. This ensures the published binaries aren't accidentally unsigned, but it cannot eliminate all SmartScreen warnings.

Verify the final downloaded artifact on Windows:

```powershell
Get-AuthenticodeSignature .\DupSweeper_Windows_x64_zh-TW_v1.4.0.exe | Format-List Status,SignerCertificate
Get-AuthenticodeSignature .\DupSweeper_Windows_x64_en_v1.4.0.exe | Format-List Status,SignerCertificate
```

`Status` must be `Valid`. If the file is unsigned, do not claim it has a verified publisher. Do not remove Mark of the Web, disable Defender, create blanket allowlists or tell users to bypass system protection.
