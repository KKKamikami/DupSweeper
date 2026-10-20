# 檔案整理助手｜獨立最終版

**找重複檔案、比較照片與影片、智慧選擇保留版本。刪除前一定由你確認。**

支援 Windows、macOS；所有掃描、媒體特徵與歷史紀錄在你的電腦本機處理。首次「開發／打包」需連線下載套件，**已製作完成的 EXE／APP 不需要安裝 Python**。若掃描 OneDrive 等同步資料夾，雲端服務可能自行下載雲端檔案。

## 開始使用

**Windows（建置完成後）**：下載 `FileTidy.exe`，放在任意資料夾，雙擊啟動；不需要執行 BAT、安裝 Python 或另行安裝 FFmpeg。

**macOS（建置完成後）**：下載 `FileTidy_macOS.zip`，解壓後雙擊 `FileTidy.app`。首次開啟可能受到 Gatekeeper 阻擋，請從「系統設定 → 隱私權與安全性」確認來源後選擇允許。此程式未經 Apple 公證，不能保證每台 Mac 都能直接開啟；**請只執行你信任來源的程式**。

> 本專案提供程式碼與可在相應系統自動產生原生執行檔的打包流程。Linux 環境**不能直接產生／驗證** Windows EXE 和 macOS APP；若取得的是「原始碼 ZIP」，它**不是**可直接雙擊的 EXE。原生執行檔應從下述建置作業下載。

## 五個操作步驟

1. **加入掃描位置**：選擇一顆硬碟或多個資料夾。視窗較窄時，先按右上角「展開設定」。
2. **設定優先保留資料夾（選用）**：可以加入多個，優先層級相同。群組內若有優先資料夾的檔案，先從其中保留品質較好的版本；否則從整組選最佳版。
3. **選擇掃描方式**：首次使用「完整重新掃描」，之後可使用「歷史快速檢查」查核尚未完成的已知群組；定期再執行完整重新掃描。
4. **智慧選取與人工檢查**：智慧選取僅標記候選檔案，**不會立即刪除**。雙擊檔案列可更改標記，亦可匯出 CSV。
5. **確認移至回收桶**：程式再檢查檔案狀態與內容，需你確認才開始移動。外接或網路磁碟的回收桶行為可能因系統不同而異。

## 類型判斷

| 類型 | 如何判斷 | 可否智慧標記 |
| --- | --- | --- |
| 內容完全相同 | 檔案大小、三段快速取樣、再完整 SHA-256 驗證 | 可以，至少保留一份 |
| 同名不同內容 | 名稱相同，但位元內容不同 | **只警告，不自動選取** |
| 相似照片 | Pillow 產生 dHash 視覺特徵 | 預設不標記；開啟高風險選項後才可 |
| 相似影片 | FFmpeg／FFprobe 取樣影格，搭配影片長度與比例 | 預設不標記；必須人工比對音軌、字幕與剪輯差異 |

**快取與歷史不是完整檔案庫**。歷史模式只核對先前已記錄的群組，可能略過新增檔案；「補做相似比對」會從有歷史的掃描路徑重新列舉媒體檔案，但不取代全面重新掃描。

**強制停止**：可終止獨立背景工作；如果停止時已在移動檔案，部分檔案可能已被移動，務必重新掃描確認。

## 歷史與舊版本完全隔離

此最終版**不讀取、不遷移，也不修改 v3／v4 的資料庫或設定**。開始使用時請先做一次完整重新掃描。

本版專用資料夾：

- Windows：`%LOCALAPPDATA%\FileTidyFinal\`
- macOS：`~/Library/Application Support/FileTidyFinal/`（歷史與設定）；`~/Library/Caches/FileTidyFinal/`（快取）
- Linux 原始碼測試：`~/.local/share/FileTidyFinal/`（歷史）；`~/.cache/FileTidyFinal/`（快取）

歷史記錄在 `scan_history.sqlite3`，檔案雜湊快取在 `hash_cache.sqlite3`，設定在 `settings.json`。

## 如何產出一鍵執行檔（專案作者或維護人員）

### GitHub Actions（推薦）

將本原始碼資料夾**全部上傳至自己的 GitHub 儲存庫根目錄**，進入 **Actions → Build one-click Windows and macOS apps → Run workflow**。建置成功後在該次工作頁的 **Artifacts** 取得：

- `FileTidy_Windows_EXE`：內含 `FileTidy.exe`，Windows 雙擊執行。
- `FileTidy_macOS_AppleSilicon_APP` 或 `FileTidy_macOS_Intel_APP`：依 Mac 晶片類型選擇，內含 `FileTidy_macOS.zip`，解壓後可雙擊 `.app`。

工作流程使用 Windows / macOS 原生建置環境，包含 Pillow、Send2Trash 和 FFmpeg/FFprobe，並執行 `--self-test` 驗證基本比對。Windows 建置時驗證 FFmpeg 發行者提供的 SHA-256 校驗碼。

### 自己在 Windows 建置

安裝 **Python 3.11 或更新版本**，開 PowerShell 執行：

```powershell
./packaging/build_windows.ps1
```

成品位置：`dist/FileTidy.exe`。

### 自己在 macOS 建置

安裝 **Python 3.11+、Homebrew**，執行：

```bash
./packaging/build_macos.sh
```

成品位置：`release/FileTidy_macOS.zip`。

### 從原始碼執行（開發者）

```bash
python3 -m pip install Pillow Send2Trash
python3 duplicate_finder.py
```

要使用相似影片功能，請自行安裝 FFmpeg 與 FFprobe，或使用上方已打包的正式執行檔。

## 安全及限制

- 刪除永遠要人工確認；相似媒體不能保證是同一作品，不可在未預覽前批次刪除。
- 系統目錄、應用程式資料夾有額外保護；資料不可讀或檔案在掃描中變動時可能略過，應查看錯誤狀態。
- 無法保證所有特殊照片格式都能由 Pillow 解碼，也無法保證所有影片都由 FFmpeg 正確分析。
- 用戶應自行備份重要資料。EXE 與 APP 未附數位簽章或 Apple 公證；下載後請確認來源。
- 本軟體使用 FFmpeg（[ffmpeg.org](https://ffmpeg.org/)），其散布授權取決於實際建置配置。若對外散布含 FFmpeg 的執行檔，請一併遵循該版本的 LGPL/GPL 授權與相應原始碼提供義務。

## 測試

```bash
python3 -m pip install pytest
python3 -m pytest -q tests
```

圖形介面可在支援 Tk 的桌面環境執行 `python3 tests/gui_smoke.py` 等測試。
