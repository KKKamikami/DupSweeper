# DupSweeper

[English](#english-documentation) | [繁體中文](#中文說明)

---

## English Documentation

A cross platform GUI tool to find duplicate files compare photos and videos and smartly select versions to keep All scans are processed locally on your computer and files are never deleted without your confirmation

### Project Files Description

| File or Folder | Description |
| :--- | :--- |
| `duplicate_finder.py` | Main graphical user interface application entry point |
| `duplicate_engine.py` | Core comparison engine handling file hashing image analysis and video fingerprinting |
| `history_store.py` | SQLite database manager for saving scan history and supporting resume functionality |
| `packaging` | Automated build scripts for generating standalone Windows EXE and macOS APP bundles |
| `tests` | Automated test suite for verifying engine accuracy GUI responsiveness and resume features |
| `requirements-build.txt` | Python package dependencies required for building standalone executables |

### How the Program Works

* **Multi Stage Filtering** First groups files by byte size then computes fast partial hashes and finally verifies full cryptographic hashes or perceptual media signatures to avoid unnecessary disk reads
* **Smart Media Analysis** Integrates FFmpeg and image libraries to extract visual frames and audio features allowing it to detect duplicate photos and videos even if their filenames or formats differ
* **History and Resume Store** Saves scan progress and file signatures in a local database so interrupted scans can resume instantly and future checks only process newly added or modified files
* **Smart Retention Rules** Evaluates priority folders media resolution and file modification time to automatically recommend the best version to keep in each duplicate group

### Installation and Operation

#### 1 Standalone Installation for General Users
* **Windows** Go to the Releases page download `FileTidy.exe` place it in any folder and double click to launch No Python or FFmpeg installation is required
* **macOS** Go to the Releases page download `FileTidy_macOS.zip` extract it and double click `FileTidy.app` If blocked by macOS Gatekeeper on first launch go to System Settings then Privacy and Security to allow it

#### 2 Run from Source for Developers
* Install Python 3 and run `pip install -r requirements-build.txt` in your terminal
* Run `python duplicate_finder.py` to launch the graphical interface directly

#### 3 Five Operation Steps
1. **Add Scan Locations** Select one drive or multiple folders to scan If the window is narrow click Expand Settings at the top right first
2. **Set Priority Folders** Optional Add one or more preferred folders When duplicates are found files inside priority folders will be kept first
3. **Select Scan Mode** Choose Full Rescan for the first run Later you can use Quick History Check to verify known groups or Incremental Scan to check new files
4. **Review and Confirm** Inspect the detected duplicate groups preview photos or videos side by side and verify which files are marked for keeping
5. **Execute Cleanup** Confirm your selections to safely move unwanted duplicates to the trash or delete them permanently

---

## 中文說明

跨平台重複檔案搜尋與整理工具 支援尋找重複檔案 比較照片與影片 並智慧選擇最佳保留版本 所有掃描皆在你的電腦本機處理 刪除前一定經過你的確認

### 檔案結構描述

| 檔案或資料夾名稱 | 功能說明 |
| :--- | :--- |
| `duplicate_finder.py` | 圖形化使用者介面主程式與啟動入口 |
| `duplicate_engine.py` | 核心比對引擎 負責檔案雜湊計算 圖片相似度分析與影片特徵擷取 |
| `history_store.py` | 歷史紀錄管理模組 負責儲存掃描進度以支援斷點續傳與快速檢查 |
| `packaging` | 跨平台自動化打包腳本 用於製作獨立的 Windows 執行檔與 macOS 應用程式 |
| `tests` | 自動化測試程式集 用於驗證比對引擎準確度 介面反應與續傳功能 |
| `requirements-build.txt` | 開發與打包獨立執行檔所需的 Python 套件清單 |

### 程式運作原理

* **多階段加速篩選** 先比對檔案大小快速排除獨立檔案 接著計算局部特徵碼 最後才進行完整雜湊或影音內容比對 大幅減少硬碟讀取時間
* **智慧影音特徵比對** 整合 FFmpeg 與影像處理技術 擷取照片與影片的視覺畫面進行比對 即使檔名不同或格式轉換也能精準抓出重複影音
* **歷史資料庫與斷點續傳** 將掃描過的檔案特徵與進度寫入本機資料庫 大型硬碟掃描中斷後可直接接續進度 日後也能只針對新增或修改的檔案進行快速比對
* **智慧保留決策機制** 根據使用者設定的優先保留資料夾 畫質解析度與檔案時間 自動在重複群組中勾選最值得保留的最佳版本

### 程式安裝與操作方式

#### 1 一般使用者免安裝執行版
* **Windows 系統** 前往 Releases 頁面下載 `FileTidy.exe` 放在任意資料夾並雙擊啟動 不需要執行批次檔也不用安裝 Python 或 FFmpeg
* **macOS 系統** 前往 Releases 頁面下載 `FileTidy_macOS.zip` 解壓縮後雙擊 `FileTidy.app` 首次開啟若受到系統阻擋 請從系統設定進入隱私權與安全性選擇允許開啟

#### 2 開發者原始碼執行方式
* 確保電腦已安裝 Python 3 並在終端機執行 `pip install -r requirements-build.txt` 安裝依賴套件
* 在終端機執行 `python duplicate_finder.py` 即可直接啟動圖形化介面

#### 3 五個操作步驟
1. **加入掃描位置** 選擇一顆硬碟或多個資料夾 視窗較窄時可先按右上角展開設定按鈕
2. **設定優先保留資料夾** 選用功能 可加入多個資料夾 群組內若有位於優先資料夾的檔案會優先保留該處品質較好的版本
3. **選擇掃描方式** 首次使用請選完整重新掃描 之後可使用歷史快速檢查核對尚未處理的群組 或使用增量掃描加速檢查新檔案
4. **預覽與確認保留項目** 點擊重複群組預覽照片或影片 檢查系統自動挑選的保留版本是否符合需求
5. **執行安全清理** 確認勾選無誤後執行移除 釋放硬碟空間