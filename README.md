# DupSweeper

**Local duplicate file finder for Windows, macOS, and Ubuntu.**

[Download releases](https://github.com/KKKamikami/DupSweeper/releases) · [English](#english) · [繁體中文](#繁體中文)

## English

DupSweeper helps reclaim disk space by finding **exact duplicate files**, **duplicate photos**, and **visually similar videos** without uploading personal files to the cloud. Scan hard drives, external disks, or selected folders with a clean desktop interface.

### Features

- **Accurate duplicate detection:** multi-stage filtering and full SHA-256 verification, including files with different names or extensions.
- **Photo and video duplicate finder:** optional local visual fingerprints using Pillow and FFmpeg. Similarity is not proof of identical video content or audio.
- **Folder exclusion / allowlist:** exclude multiple folders and subfolders before scanning, or scan everything and hide those folders from the results. Excluded files cannot be marked or selected for cleanup.
- **Smart selection:** keep a preferred copy using multiple priority folders and media quality; configure trusted photo and video selection separately.
- **Scan history:** revisit previously detected groups; run a full scan to discover newly added files.
- **Safe disk cleanup:** review before moving candidates to the system Trash. Supports force stop and CSV export.
- **Adaptive desktop interface:** settings use clear tabs on compact windows and 2×2 cards on large displays. Text wraps automatically and no settings sidebar scroll is required.
- **Local-first:** no account, cloud scan, or file upload is required.

### Downloads

| Operating system | Release file |
|---|---|
| Windows x64 (Traditional Chinese) | `DupSweeper_Windows_x64_zh-TW_v1.4.0.exe` |
| Windows x64 (English) | `DupSweeper_Windows_x64_en_v1.4.0.exe` |
| macOS (Apple Silicon / Intel) | `DupSweeper_macOS_v1.4.0.zip` |
| Ubuntu | `DupSweeper_Ubuntu_v1.4.0.deb` |

Download the files under [Releases](https://github.com/KKKamikami/DupSweeper/releases) **after the builds succeed**. The GitHub project ZIP contains source code, not a Windows executable.

### How to use

1. Add one or more scan locations.
2. Add **Excluded Folders** (optional). Leave *Skip excluded folders during scan* checked for faster scans; uncheck to scan all files while hiding excluded paths afterward. Excluded folders and their children never appear in results or Smart Select.
3. Add preferred folders (optional), then select **Full Rescan**. For existing results you can add or remove excluded folders without rescanning; any previous cleanup marks are cleared.
4. Run **Smart Select**, check the recommendations, and confirm before moving anything to Trash.

The exclusion settings are saved locally. Quick History Check is scoped to the scan locations **and the exclusions used during scanning**. If the scope changes, use Full Rescan. Visual similarity may be imperfect: back up important media before removal.

### Windows security

Unsigned GitHub-hosted EXEs may trigger Microsoft Defender SmartScreen. Legitimate Authenticode code signing and reputation reduce this risk but cannot guarantee that no warnings appear. Microsoft Store distribution of an approved MSIX app is Microsoft's recommended option for avoiding SmartScreen download warnings. See [WINDOWS_SECURITY.md](WINDOWS_SECURITY.md). Never disable Defender to run this app.

### Source code

Requires Python 3.10+, Tkinter, Pillow, Send2Trash and optionally FFmpeg/FFprobe. Run `python dupsweeper.py --lang en` (English) or `python dupsweeper.py` (Traditional Chinese).

## 繁體中文

DupSweeper 是一款**重複檔案搜尋、重複照片比對與相似影片整理工具**，適用於 Windows、macOS、Ubuntu。支援硬碟、外接磁碟及自訂資料夾，所有掃描與影像比對均在本機處理。

### 主要功能

- **精準找重複**：檔案大小、快速抽樣及完整 SHA-256 驗證，即使檔名或副檔名不同也能辨識。
- **相似照片／影片**：使用 Pillow 與 FFmpeg 分析視覺特徵，支援照片重複清理及影片重複比對；視覺相似不等於影音完全相同。
- **多資料夾白名單／排除清單**：掃描前可略過指定資料夾和所有子資料夾；也可先完整掃描，之後從結果中隱藏排除位置，且不讓智慧選取或回收桶處理它們。
- **智慧保留**：支援多個優先保留資料夾，依畫質建議保留版本；照片及影片可分開設定信任智慧選取。
- **歷史快速檢查**：加速處理已知重複群組；找新檔案仍需完整重新掃描。
- **安全整理硬碟**：人工總確認後移至回收桶，支援強制停止與 CSV 匯出。
- **自動調整介面**：小視窗使用可切換的設定分頁，大型視窗使用 2×2 卡片；說明文字自動換行。

### 下載

請至 [Releases](https://github.com/KKKamikami/DupSweeper/releases) 依照上方表格下載對應系統版本。專案原始碼 ZIP 不等同於 Windows EXE。

### 使用方式

1. 加入要掃描的硬碟或資料夾。
2. 在「排除資料夾／白名單」加入多個不想處理的位置。預設勾選「掃描前略過排除資料夾」可節省時間；取消勾選則會掃描全部，但不顯示白名單檔案。
3. 可另外指定多個優先保留資料夾，再按「完整重新掃描」。掃描後變更白名單可立即更新畫面，原先標記會清空。
4. 按「智慧選取」，確認要移除的副本，再按「確認移至回收桶」。

白名單設定會保存在本機。歷史快速檢查須使用**相同掃描位置及掃描排除範圍**，否則應重新完整掃描。視覺相似仍有誤判可能，重要資料請先備份。

### Windows 警告

未經簽署的 EXE 可能被 Microsoft Defender SmartScreen 提醒。受信任的數位簽章與正常發行信譽可以降低警告，但無法保證完全消失。詳見 [WINDOWS_SECURITY.md](WINDOWS_SECURITY.md)，請勿為了使用程式而停用 Defender。

### 原始碼啟動

需要 Python 3.10 以上、Tkinter、Pillow、Send2Trash；相似影片功能另需 FFmpeg／FFprobe。執行 `python dupsweeper.py`，英文介面使用 `python dupsweeper.py --lang en`。

---

## License

DupSweeper is licensed under the MIT License.

Copyright (c) 2026 KKKamikami

Original project: https://github.com/KKKamikami/DupSweeper

**Keywords:** duplicate file finder, duplicate photo finder, duplicate video finder, disk cleanup, file deduplication, SHA-256, perceptual hashing, FFmpeg, local file manager, Windows, macOS, Ubuntu, 重複檔案, 重複照片, 相似影片, 硬碟清理, 智慧選取。
