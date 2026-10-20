"""Local UI English/Traditional Chinese strings; no network translation."""
import os

_LANGUAGE = 'zh-TW'

_TRANSLATIONS = {'重複檔案整理': 'Duplicate File Manager', '找重複、選保留、確認後移除': 'Find duplicates · Choose what to keep · Clean safely', '本機處理': 'On-device processing', '歷史快速檢查': 'Quick History Check', '完整重新掃描': 'Full Rescan', '補做相似比對': 'Complete Media Scan', '查看歷史': 'Scan History', '安全停止': 'Stop Safely', '強制停止': 'Force Stop', '就緒：請加入掃描位置。': 'Ready — add a drive or folder to scan.', '掃描位置': 'Scan locations', '+ 加入': '+ Add', '移除': 'Remove', '清空': 'Clear', '優先保留的資料夾（可多選）': 'Preferred folders (multiple allowed)', '相似照片與影片': 'Similar photos and videos', '尚無掃描結果': 'No scan results yet', '群組／檔案': 'Group / File', '建議': 'Recommendation', '大小': 'Size', '畫質': 'Quality', '位置': 'Location', '顯示更多結果': 'Show more results', '智慧選取': 'Smart Select', '標記所選': 'Mark Selected', '清除標記': 'Clear Marks', '確認移至回收桶': 'Move to Trash', '開啟檔案位置': 'Open File Location', '複製路徑': 'Copy Path', '匯出 CSV': 'Export CSV', '待移除：0 份': 'To remove: 0 files', '待移除：': 'To remove: ', ' 份｜': ' files | ', '信任設定已變更，舊標記已清空；請重新智慧選取。': 'Trust settings changed. Previous marks cleared; run Smart Select again.', '標記已清空': 'Marks Cleared', '優先保留位置已改變，請重新執行智慧選取。': 'Preferred folders changed; please run Smart Select again.', '新增智慧保留優先資料夾': 'Choose Preferred Folder', '完整掃描時間': 'Full scan date', '原進階模式': 'Media scan', '已補掃': 'Media resumed', '掃描份數': 'Files scanned', '群組數': 'Groups', '選取硬碟或資料夾': 'Choose a Drive or Folder', '尚未指定掃描位置': 'Scan Location Missing', '請先加入至少一個資料夾或硬碟。': 'Add at least one folder or drive first.', '尚未設定掃描位置': 'Scan Location Missing', '請先選擇有完整掃描歷史的資料夾。': 'Choose a previously scanned folder first.', '補做上次跳過的相似分析': 'Complete Previously Skipped Media Scan', '歷史未儲存完整檔案清單。': 'The history does not include the entire file inventory.', '程式將使用這筆歷史的路徑，重新找出照片與影片並補算視覺特徵。': "DupSweeper will rescan photos and videos from this history's paths.", '一般檔案不重新計算完整 SHA-256，原本完整掃描歷史會保留。': 'Other files will not be fully rehashed. Your original scan history is preserved.', '這仍需要時間，且不代表全部新檔案已完成精確重複搜尋。是否繼續？': 'This may take time and does not fully check new files for exact duplicates. Continue?', '已要求安全中斷，正在結束目前操作；如未及時停止可按「強制停止」。': 'Safe stop requested. Finishing current work. Use Force Stop if needed.', '確認強制停止': 'Confirm Force Stop', '強制停止將立即終止掃描／移動程序。若正在移至回收桶，部分檔案可能已移動，必須重新掃描才能繼續。': 'Force Stop immediately ends the scan or trash operation. Some files may already have moved; rescan before continuing.', '確定強制停止？': 'Force stop now?', '已強制停止移動程序；狀態可能部分更新，請重新掃描。': 'Trash operation was interrupted. Please rescan.', '請重新掃描': 'Please Rescan', '移動中途被強制停止，結果已清空；請重新掃描確認檔案位置。': 'Trash operation stopped midway. Results cleared; rescan to verify files.', '已強制停止掃描，未進行任何刪除。': 'Scan stopped. No files deleted.', '尚無掃描結果。': 'No scan results yet.', '媒體補掃＋歷史結果（不包含新檔精確比對）｜': 'Media resume + history (new exact duplicates not checked) | ', '歷史待處理（未包含新檔精確比對）｜': 'Known history only (new exact duplicates not checked) | ', '系統位置（保護）': 'Protected system location', '✓ 待移至回收桶': '✓ Marked for Trash', '⚠ 僅同名，不可推定重複': '⚠ Same filename only — not a duplicate', '△ 視覺近似，需確認': '△ Visually similar — verify', '系統或程式資料夾不允許刪除。': 'Protected system or application folder; removal prohibited.', '同名不同內容只是警示，不能作為移除依據。': 'Same filename with different content is only a warning, not grounds for removal.', '此相似類型未啟用；若要個別標記，請勾選「允許手動標記其他相似媒體」。': 'This media type is not trusted. Enable manual marking if you wish to review and mark it.', '不允許標記': 'Cannot Mark', '已略過部分選取': 'Some Files Skipped', '相似照片／圖片': 'Similar photos/images', '相似影片': 'Similar videos', '已標記 ': 'Marked ', ' 份，尚未移除。': ' files (not removed).', '智慧信任類型：': 'Trusted media types: ', '未信任的相似類型不會自動標記；移至回收桶前仍會有一次總確認。': 'Untrusted media is not automatically marked. One final confirmation is always required.', '無（僅精確重複）': 'None (exact duplicates only)', '智慧選取已完成': 'Smart Selection Complete', '尚未標記': 'No Files Marked', '請手動標記檔案或點選「智慧選取」。': 'Mark files manually or choose Smart Select.', '缺少回收桶套件': 'Trash Support Unavailable', '未安裝必要元件 send2trash。請使用正式安裝包或參閱 README.md。': 'Required dependency send2trash is missing. Use a packaged release or consult README.md.', '不會改用永久刪除。': 'Permanent deletion will not be substituted.', '即將把 ': 'About to move ', ' 份檔案（': ' files (', '）移至作業系統回收桶。': ') to the system Trash.', '目前為歷史結果，未檢查新加入檔案；移動前會重新驗證原始檔案的雜湊。': 'History results may omit newly added files; hashes will be revalidated before moving.', '其中 ': 'Of those, ', ' 份僅屬視覺相似，可能有不同的音軌／字幕，無法保證是同一檔案。': ' files are only visually similar; audio/subtitles may differ.', '移動前會重新驗證來源與保留副本，且不會永久刪除。': 'Source and retained files are revalidated before moving; no permanent deletion.', '外接／網路磁碟不一定支援復原。確定嗎？': 'Removable/network drives might not allow recovery. Continue?', '最後確認': 'Final Confirmation', '未信任相似媒體二次確認': 'Additional Confirmation for Untrusted Similar Media', '若已自行確認內容，請輸入：確認相似': 'If you verified the content, type: CONFIRM SIMILAR', '確認相似': 'CONFIRM SIMILAR', '準備重新驗證檔案並移至回收桶…': 'Revalidating files before moving to Trash…', '找不到檔案': 'File Not Found', '請重新掃描。': 'Please rescan.', '已複製 ': 'Copied ', ' 條檔案路徑。': ' file paths.', '匯出所有結果': 'Export All Results', '檔案整理清單.csv': 'DupSweeper_results.csv', '展開設定': 'Expand Settings', '收合設定': 'Collapse Settings', '偏好設定未儲存': 'Could Not Save Settings', '無法讀取歷史': 'Unable to Read History', '先選擇紀錄': 'Select a Record', '請先點選一筆歷史掃描紀錄。': 'Please select a history record first.', '有掃描路徑不存在': 'Scan Path Not Found', '已載入掃描位置；可按「補做上次跳過的相似比對」。': 'Scan locations loaded. You can now complete skipped media analysis.', '尚無符合的歷史紀錄': 'No Matching Scan History', '可省 ': 'Potential savings: ', '精確重複 ': 'Exact duplicates: ', ' 組／多餘 ': ' groups / extra ', ' 份／可省 ': ' files / save ', '｜相似媒體 ': ' | similar media: ', ' 組｜同名不同內容警示 ': ' groups | same-name warnings: ', ' 組': ' groups', '★ 優先資料夾保留': '★ Keep (preferred folder)', '★ 品質優先保留': '★ Keep (best quality)', '安全檢查未通過': 'Safety Check Failed', ' 份手動標記的相似檔案未啟用信任。': ' manually marked similar files are not trusted.', '無法開啟': 'Unable to Open', 'CSV 已儲存：': 'CSV saved: ', '無法匯出': 'Export Failed', '背景作業正在執行': 'Background Task Running', '結束視窗將強制中止背景作業；若正在移動檔案，應重新掃描。': 'Closing now force-stops background work. Rescan if files were being moved.', '確定結束？': 'Quit anyway?', '優先保留這些位置中較好的版本。': 'Keep the best copy from preferred folders first.', '啟用相似媒體分析': 'Enable visual similarity analysis', '智慧選取相似照片／圖片（信任）': 'Trust Smart Select for similar photos/images', '智慧選取相似影片（信任）': 'Trust Smart Select for similar videos', '允許手動標記其他相似媒體': 'Allow manual marking of other similar media', '勾選的相似類型不需逐組審核；移至回收桶仍須總確認。': 'Trusted types skip group-by-group review. Final Trash confirmation remains required.', '搜尋：': 'Search:', '選擇本版完成的掃描紀錄，可載入掃描位置或補做相似媒體比對。': 'Select a completed scan to load locations or complete the media analysis.', '請確認磁碟已連接且磁碟代號沒有變更。': 'Check the drive is connected and its letter has not changed.', '載入掃描位置': 'Load Scan Locations', '載入並立即補掃相似媒體': 'Load and Resume Media Scan', '關閉': 'Close', '載入更多群組（已顯示 ': 'Load more groups (showing ', ' 份）': ' files)', '禁止移除系統位置：': 'Protected location — cannot remove: ', '群組全部檔案被選取，請至少取消一份：': 'All group files marked; keep at least one: ', 'CSV 檔案': 'CSV files', '群組': 'Group', '類型': 'Type', '檔案名稱': 'Filename', '狀態': 'Status', '大小(位元組)': 'Size (bytes)', '畫質資訊': 'Media quality', '修改時間': 'Modified', '完整路徑': 'Full path', '精確SHA256': 'Exact SHA-256', '有': 'Yes', '無': 'No', '背景工作異常結束；如有移動操作，請重新掃描。': 'Background worker exited unexpectedly. Rescan if any files were moved.', '至少保留一份內容相同的檔案：': 'Keep at least one exact duplicate: ', '不允許僅憑檔名判定可刪除：': 'Cannot remove by filename alone: ', '相似媒體群組必須至少保留一份：': 'Keep at least one similar-media copy: ', '部分相似比對未執行': 'Some Similarity Checks Were Skipped', '處理完成': 'Operation Finished', '部分歷史內容無法沿用': 'Some History Records Are Invalid', '歷史紀錄未儲存': 'History Not Saved', 'Pillow（相似照片）': 'Pillow (similar photos)', 'FFmpeg＋FFprobe（相似影片）': 'FFmpeg + FFprobe (similar videos)', '精確重複與同名警示仍正常。請參考 README.md 安裝。': 'Exact duplicates and same-name warnings still work. See README.md.', '已移至回收桶 ': 'Moved to Trash: ', ' 份，失敗 ': ' files, failed: ', ' 份。為防止結果過期，請重新掃描。': ' files. Please rescan to refresh results.', '媒體已重列舉；新檔案的精確重複仍須完整掃描。': 'Media files were re-enumerated. New exact duplicates require a full scan.', '新增檔案未檢查。': 'Newly added files were not checked.', '已變更的群組：': 'Changed groups: ', '所有已知副本都消失的群組：': 'Groups with no remaining known copies: ', '這些群組已跳過，沒有自動標記。請使用「完整重新掃描」查清楚。': 'These groups were skipped without marking. Run a Full Rescan.', '｜略過硬連結 ': ' | skipped hard links: ', '｜例外 ': ' | errors: ', ' 筆': ' entries', '缺少：': 'Missing: ', '已移至回收桶：': 'Moved to Trash: ', '未成功：': ' files', '已停止。': 'Stopped.', '作業錯誤': 'Operation Error', '補掃媒體完成｜': 'Media scan completed | ', '歷史紀錄（': 'History (', '）：未處理精確 ': '): unresolved exact ', ' 組／已處理略過 ': ' groups / processed ', ' 組｜自動標記 ': ' groups / auto-marked ', ' 份｜異動需重掃 ': ' files / changed ', ' 組｜全部缺失 ': ' groups / missing ', ' 組。': ' groups.', '｜分析媒體 ': ' | media analyzed: ', ' 份；失敗 ': ' files; failures: ', ' 份。': ' files.', '完整掃描完成：': 'Full scan finished: ', ' 份檔案｜': ' files | ', '歷史儲存失敗': 'History save failed', '已建立新歷史': 'New history saved', '錯誤：': 'Error: ', '內容完全相同': 'Exact duplicates', '同名但內容不同！': 'Same filename, different content!', '相似照片（人工判讀）': 'Similar photos (visual)', '相似影片（人工判讀）': 'Similar videos (visual)', '完整結果｜': 'Full results | ', '○ 精確重複副本': '○ Exact duplicate copy', '另有重複': 'Other duplicates', '編碼': 'Encoding', '檔案': 'File', '參考': 'Reference'}


_TRANSLATIONS.update({
    '完整掃描歷史':'Full Scan History',
    '優先保留':'Preferred Folders',
    '相似媒體':'Similar Media',
    '完整重新掃描：不讀取歷史紀錄與 SHA 快取，檢查範圍內所有可存取檔案。':
        'Full Rescan: checking all accessible files without old history or SHA cache.',
    '正讀取本版歷史，補掃原磁碟中的照片／影片；可強制停止。':
        'Reading history and rescanning photos and videos. Force Stop is available.',
    '歷史檢查只核對已記錄群組；要補做先前未完成的照片／影片分析，請選擇補做相似比對。':
        'Quick History Check verifies known groups only. Use Complete Media Scan for unfinished photo/video analysis.',
    ' 秒｜':' sec | ',
    ' 份\n未成功：':' files\nFailed: ',
    ' 份\n\n請重新掃描。':' files\n\nPlease rescan.',
})

_TRANSLATIONS.update({
    '列舉資料夾':'Enumerating folders',
    '列舉完成':'Enumeration complete',
    '快速抽樣（首／中／尾）':'Fast sampling (start/middle/end)',
    '完整 SHA-256 驗證':'Full SHA-256 verification',
    '進階媒體分析（可略過）':'Advanced media analysis (optional)',
    '核對歷史檔案':'Checking history files',
    '補掃媒體檔案清單':'Enumerating media files',
    '媒體檔案清單完成':'Media inventory complete',
    '補做相似照片／影片比對':'Completing media similarity checks',
    '移至回收桶':'Moving to Trash',
    '視覺相似，可能有不同音軌、字幕或內容；刪除須另外確認':
        'Visually similar; audio, subtitles or content may differ. Verify before removal.',
    '僅同名，內容不相同；不可僅憑此項進行刪除':
        'Same filename, different contents; do not remove based on filename alone.',
    '歷史紀錄版本已過期，請執行「完整重新掃描」。':'History format is outdated. Please run Full Rescan.',
    '歷史紀錄無法讀取，請執行「完整重新掃描」。':'History cannot be loaded. Please run Full Rescan.',
    '此歷史尚未補做相似分析。請按「補做相似比對」。':
        'This history lacks media analysis. Choose Complete Media Scan.',
    '缺少 FFmpeg 或 FFprobe。請重新執行 Windows 啟動檔安裝，再補掃。':
        'FFmpeg or FFprobe is missing. Install required media tools and try again.',
    '缺少 Pillow，請重新執行 Windows 啟動檔以安裝。':
        'Pillow is missing. Install it and retry.',
})

_TRANSLATIONS.update({
    '排除資料夾': 'Excluded Folders',
    '｜排除：': ' | skipped: ',
    '排除資料夾／白名單': 'Excluded folders / Allowlist',
    '掃描前略過排除資料夾': 'Skip excluded folders during scan',
    '排除資料夾及子資料夾不會出現在結果，也不會被智慧選取。取消上方勾選可全碟掃描後再隱藏。':
        'Excluded folders and subfolders never appear in results or Smart Select. Uncheck to scan everything but hide excluded paths afterward.',
    '加入排除資料夾': 'Add an excluded folder',
    '排除範圍已更新，先前標記已清空；歷史比對須使用相同的掃描排除設定。':
        'Exclusions updated. Marks cleared. Quick History Check requires matching scan exclusions.',
    '已排除的資料夾不可標記移除。': 'Excluded files cannot be marked for removal.',
    '禁止移除排除資料夾內的檔案：': 'Cannot remove a file within an excluded folder: ',
    '排除資料夾不能作為保留版本：': 'An excluded folder cannot be used as the retained copy: ',
})

def set_language(code):
    global _LANGUAGE
    _LANGUAGE = 'en' if str(code).lower().startswith('en') else 'zh-TW'

def get_language():
    return _LANGUAGE

def T(value):
    text=str(value)
    if _LANGUAGE != 'en': return text
    if text in _TRANSLATIONS: return _TRANSLATIONS[text]
    for old, new in sorted(_TRANSLATIONS.items(),key=lambda pair:len(pair[0]),reverse=True):
        if len(old) >= 3 and old in text: text=text.replace(old,new)
    return text
