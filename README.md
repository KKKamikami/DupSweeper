# DupSweeper

**v1.2.0** · [Releases](https://github.com/KKKamikami/DupSweeper/releases) · [English](#english) | [繁體中文](#繁體中文)

## English

DupSweeper is an offline desktop duplicate-file organizer for Windows, macOS, and Ubuntu. It uses full SHA-256 for exact duplicates and local photo/video signatures to suggest visually similar media. All removal decisions require final confirmation and use the system Trash where available.

### What's new in v1.2.0

- **Clearer, responsive interface:** muted pastel cards; no scrollable left settings pane. On narrow screens, use the clearly labeled Scan, Preferred and Media tabs.
- **High-DPI improvements:** Windows DPI awareness and larger, sharper fonts.
- **Proper checked icon:** selectable media options show a visible white check mark rather than an X.
- **Separate English Windows executable:** native English buttons, messages, status, and columns. Traditional Chinese remains available separately.
- **Signing-ready workflow:** optional certificate-based Authenticode signing. An unsigned EXE may trigger Microsoft Defender SmartScreen; signatures do not guarantee immediate reputation.

### Downloads

After [GitHub Actions](https://github.com/KKKamikami/DupSweeper/actions) successfully builds the release, find these files under [Releases](https://github.com/KKKamikami/DupSweeper/releases):

| System | Release asset |
|---|---|
| Windows x64 — Traditional Chinese | `DupSweeper_Windows_x64_zh-TW_v1.2.0.exe` |
| Windows x64 — English | `DupSweeper_Windows_x64_en_v1.2.0.exe` |
| macOS — Intel and Apple Silicon | `DupSweeper_macOS_v1.2.0.zip` |
| Ubuntu — DEB package | `DupSweeper_Ubuntu_v1.2.0.deb` |

Windows EXEs bundle Python, Pillow and FFmpeg. The Ubuntu DEB uses system dependencies. The macOS ZIP contains separate Intel and Apple Silicon APP archives. They should be tested on their respective target systems after each build.

### Usage

1. Add scan locations; optionally set multiple preferred folders.
2. Choose **Full Rescan** for new files; **Quick History Check** only examines known duplicate groups.
3. Enable **visual similarity analysis** if desired. You may separately trust Smart Select for photos/images and videos.
4. Use **Smart Select** or manually mark copies; confirm once before moving anything to Trash.
5. Important: visual similarity is not byte equality. Similar videos may differ in audio, subtitles or edits. Back up important files.

### Run from source

Install Python 3.10+, Tkinter, Pillow, Send2Trash and FFmpeg. Run `python dupsweeper.py --lang en` (English) or `python dupsweeper.py` (Traditional Chinese).

## 繁體中文

DupSweeper 是支援 Windows、macOS、Ubuntu 的本機重複檔案整理工具，使用 SHA-256 辨識內容完全相同的檔案，並可分析相似照片及影片。刪除候選檔案前會再次確認，採用移至系統回收桶方式處理。

### v1.2.0 更新內容

- **重新設計介面**：低飽和馬卡龍色、清楚的資訊卡片；不再使用會隱藏選項的左側設定捲軸。窄視窗改為「掃描位置／優先保留／相似媒體」分頁。
- **高清晰度文字**：Windows 高 DPI 支援、更適合閱讀的字型及間距。
- **清楚的勾選**：改用勾勾圖示，不再使用容易誤會的 X。
- **Windows 雙語版本**：繁中與英文分別打包，英文版的控制項與主要對話框均為英文。
- **正式簽署支援**：GitHub Actions 可選用程式碼簽署憑證；未簽署的 EXE 可能受到 SmartScreen 警告，數位簽署也不能保證立刻消除警告。

### 下載檔案

| 系統 | 檔案 |
|---|---|
| Windows x64 繁體中文 | `DupSweeper_Windows_x64_zh-TW_v1.2.0.exe` |
| Windows x64 English | `DupSweeper_Windows_x64_en_v1.2.0.exe` |
| macOS Apple Silicon／Intel | `DupSweeper_macOS_v1.2.0.zip` |
| Ubuntu | `DupSweeper_Ubuntu_v1.2.0.deb` |

下載前請確定 GitHub Actions 已成功建置。macOS ZIP 內有兩種晶片的 APP 壓縮包，Ubuntu 安裝時會透過系統套件管理員安裝依賴。

### 使用方法

1. 加入要掃描的硬碟或資料夾，並可指定多個優先保留資料夾。
2. 首次請用「完整重新掃描」；「歷史快速檢查」只檢查過去已知的群組。
3. 可以分別選擇是否信任智慧選取相似照片與相似影片。
4. 智慧選取後確認標記，再執行「移至回收桶」。
5. 相似影片可能含不同音訊、字幕或剪輯，仍有誤判風險，請先備份重要檔案。

### 原始碼啟動

安裝 Python 3.10 以上、Tkinter、Pillow、Send2Trash、FFmpeg，執行 `python dupsweeper.py`。英文介面可使用 `python dupsweeper.py --lang en`。

### 打包與發布

手動上傳整個專案（含 `.github/workflows/build-native.yml`）至 GitHub，於 **Actions → Build DupSweeper 1.2.0 desktop releases → Run workflow** 進行跨平台建置。下載 `DupSweeper_Release_v1.2.0` Artifact，解壓後將 4 個檔案放入 Releases `v1.2.0`。

**注意：** 專案 ZIP 是開發者程式包，不是 Windows EXE。Windows 與 macOS 原生執行檔需由對應系統的 GitHub runner 建立並檢驗。
