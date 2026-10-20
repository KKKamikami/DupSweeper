# DupSweeper

**Version 1.1.1** · [Releases](https://github.com/KKKamikami/DupSweeper/releases)

[English](#english-documentation) | [繁體中文](#中文說明)

---

## English Documentation

DupSweeper is a cross-platform GUI tool for finding exact duplicate files and visually similar photos or videos. It recommends which versions to keep and processes scans locally. Files are moved to Trash only after your confirmation.

### Project Files Description

| File or Folder | Description |
| :--- | :--- |
| `dupsweeper.py` | Main graphical user interface and entry point |
| `dupsweeper_engine.py` | Duplicate detection, hashing, photo analysis and video frame signatures |
| `dupsweeper_history.py` | Local SQLite scan-history database |
| `packaging/` | Build scripts for Windows, macOS and Ubuntu |
| `.github/workflows/` | GitHub Actions builds for the three operating systems |
| `tests/` | Automated tests |
| `requirements-build.txt` | Dependencies for building standalone applications |

### How the Program Works

* **Multi-Stage Filtering** Groups by file size, compares partial samples, then uses full SHA-256 hashes to confirm exact duplicates, even when filenames differ.
* **Smart Media Analysis** Uses Pillow and FFmpeg/FFprobe to compare image or video-frame signatures. Visually similar files are candidates, not proof that audio, subtitles or edits match.
* **Local Scan History** Saves completed scan results and caches locally. Quick history checks revisit known duplicate groups; a full rescan is needed to discover new files.
* **Smart Retention Rules** Prioritizes your chosen folders, then considers image or video quality to recommend one version to keep. Similar photos and videos have separate, optional trusted auto-selection switches.

### Installation and Operation

#### 1. Standalone Installation for General Users

Download a **successfully built** package from [Releases](https://github.com/KKKamikami/DupSweeper/releases):

* **Windows 10/11 (x64)** — `DupSweeper_Windows_x64_v1.1.1.exe`: download and double-click. No separate Python installation is needed.
* **macOS (Apple Silicon / Intel)** — `DupSweeper_macOS_v1.1.1.zip`: extract and select the folder matching your Mac, then extract and open `DupSweeper.app`. The unsigned/not-notarized application may require approval under System Settings → Privacy & Security.
* **Ubuntu** — `DupSweeper_Ubuntu_v1.1.1.deb`: install with your package manager. Installation may require downloading system dependencies.

> Release assets are available only after the corresponding GitHub Actions builds succeed. Scanning local files does not require uploading them to a server.

#### 2. Run from Source for Developers

* Install Python 3.10 or newer and Tkinter, then run `python -m pip install Pillow Send2Trash`. Install FFmpeg/FFprobe for similar-video analysis.
* Run `python dupsweeper.py` to open the GUI.
* Packaging dependencies: `python -m pip install -r requirements-build.txt`.

#### 3. Five Operation Steps

1. **Add Scan Locations** — Select drives or folders. Expand Settings if the window is narrow.
2. **Set Priority Folders** — Optionally add multiple folders whose files should be retained first.
3. **Choose Scan Mode** — Run a Full Rescan initially; Quick History Check revisits known groups. Run full scans periodically for newly added files.
4. **Smart Selection** — Review results or independently enable trusted auto-selection for similar photos/images and similar videos. Files with the same name but different contents are only flagged.
5. **Confirm Cleanup** — Check the selected files and confirm once to move duplicates to Trash. Similarity matching may be imperfect, so back up important files.

---

## 中文說明

**DupSweeper v1.1.1** 是跨平台的重複檔案搜尋與整理工具，支援找出內容完全相同的檔案、相似照片及影片，並智慧建議保留最佳版本。所有掃描皆在本機完成，移至回收桶前一定會請你確認。

### 檔案結構描述

| 檔案或資料夾名稱 | 功能說明 |
| :--- | :--- |
| `dupsweeper.py` | 圖形介面主程式與啟動入口 |
| `dupsweeper_engine.py` | 精確比對、圖片相似分析與影片影格特徵 |
| `dupsweeper_history.py` | 本機 SQLite 歷史紀錄 |
| `packaging/` | Windows、macOS、Ubuntu 的打包腳本 |
| `.github/workflows/` | GitHub Actions 三平台自動建置 |
| `tests/` | 自動化測試 |
| `requirements-build.txt` | 建立獨立執行檔所需的套件 |

### 程式運作原理

* **多階段加速篩選**：先按檔案大小分類，再比較局部內容，最後使用完整 SHA-256 確認；不同檔名但內容完全相同也能找到。
* **智慧影音特徵比對**：利用 Pillow 和 FFmpeg/FFprobe 比對圖片或影片影格。視覺相似不代表音軌、字幕或剪輯完全相同，仍可能誤判。
* **本機歷史紀錄**：儲存完成的掃描結果與快取。歷史快速檢查只核對已知群組，想找新檔案仍需完整重新掃描。
* **智慧保留機制**：優先保留指定的多個資料夾，再依品質挑選最佳版本；**相似照片／圖片**與**相似影片**可分別設定是否信任智慧選取。

### 程式安裝與操作方式

#### 1. 一般使用者免編譯版本

請至 [Releases 下載頁面](https://github.com/KKKamikami/DupSweeper/releases) 選擇**已成功建置**的系統版本：

* **Windows 10/11（x64）**：下載 `DupSweeper_Windows_x64_v1.1.1.exe`，雙擊即可啟動，不必另外安裝 Python。
* **macOS（Apple Silicon／Intel）**：下載 `DupSweeper_macOS_v1.1.1.zip`，解壓後選擇對應晶片版本，開啟 `DupSweeper.app`。尚未經 Apple 公證，首次啟動可能需要到「系統設定 → 隱私權與安全性」允許。
* **Ubuntu**：下載 `DupSweeper_Ubuntu_v1.1.1.deb`，使用套件管理工具安裝；首次安裝可能需要下載相依套件。

> 發行資產需在 GitHub Actions 建置成功後才會出現。掃描本機檔案不會主動上傳雲端。

#### 2. 開發者原始碼執行方式

* 安裝 Python 3.10 以上及 Tkinter，執行 `python -m pip install Pillow Send2Trash`。相似影片比對另需 FFmpeg／FFprobe。
* 執行 `python dupsweeper.py` 開啟圖形介面。
* 打包時可執行 `python -m pip install -r requirements-build.txt`。

#### 3. 五個操作步驟

1. **加入掃描位置**：選擇硬碟或資料夾；視窗較窄時可展開設定。
2. **設定優先保留資料夾**：可加入多個資料夾，優先保留其中品質較佳的版本。
3. **選擇掃描方式**：首次使用完整重新掃描；歷史快速檢查只處理已知群組，建議定期完整重掃。
4. **智慧選取**：檢查結果，或分別開啟「智慧選取相似照片／圖片」與「智慧選取相似影片」的信任選項。同名但內容不同只會標示，不會直接列為可刪副本。
5. **確認安全清理**：確認標記後，再將不需要的副本移至回收桶。相似辨識不是百分之百準確，重要檔案請先備份。

**資料位置：** 此版的歷史與快取儲存在 DupSweeper 專屬本機資料夾；由其他產品資料夾搬遷時需重新進行完整掃描。
