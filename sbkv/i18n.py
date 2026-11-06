"""多語系 (i18n) 字串定義。

支援 zh-TW (繁體中文) 與 en (English)。
"""

LANGS = {
    "zh-TW": "繁體中文",
    "en": "English",
}

STRINGS = {
    # ---- 導覽 ----
    "nav_overview": {"zh-TW": "📋 總覽", "en": "📋 Overview"},
    "nav_log": {"zh-TW": "📜 日誌", "en": "📜 Log"},
    "nav_settings": {"zh-TW": "⚙️ 設定", "en": "⚙️ Settings"},

    # ---- 工具列 ----
    "btn_refresh": {"zh-TW": "🔄 重新讀取", "en": "🔄 Refresh"},
    "btn_export": {"zh-TW": "💾 匯出報告", "en": "💾 Export Report"},

    # ---- Secure Boot 狀態 ----
    "sb_checking": {"zh-TW": "Secure Boot: 檢查中...", "en": "Secure Boot: Checking..."},
    "sb_enabled": {"zh-TW": "Secure Boot: ✅ 已啟用", "en": "Secure Boot: ✅ Enabled"},
    "sb_disabled": {"zh-TW": "Secure Boot: ❌ 未啟用", "en": "Secure Boot: ❌ Disabled"},
    "sb_unknown": {"zh-TW": "Secure Boot: ⚠️ 無法確定", "en": "Secure Boot: ⚠️ Unknown"},
    "sb_status": {"zh-TW": "Secure Boot 狀態", "en": "Secure Boot Status"},
    "enabled": {"zh-TW": "✅ 已啟用", "en": "✅ Enabled"},
    "disabled": {"zh-TW": "❌ 未啟用", "en": "❌ Disabled"},
    "unknown": {"zh-TW": "⚠️ 無法確定", "en": "⚠️ Unknown"},

    # ---- 狀態列 ----
    "ready": {"zh-TW": "就緒", "en": "Ready"},
    "loading": {"zh-TW": "載入中...", "en": "Loading..."},
    "loading_var": {"zh-TW": "讀取 {}...", "en": "Loading {}..."},
    "load_complete": {"zh-TW": "載入完成", "en": "Load Complete"},

    # ---- 總覽頁 ----
    "overview_title": {"zh-TW": "📋 Secure Boot 金鑰總覽", "en": "📋 Secure Boot Keys Overview"},
    "cert_summary": {"zh-TW": "憑證摘要", "en": "Certificate Summary"},
    "col_var": {"zh-TW": "變數", "en": "Variable"},
    "col_type": {"zh-TW": "類型", "en": "Type"},
    "col_subject": {"zh-TW": "Subject / 雜湊", "en": "Subject / Hash"},
    "col_idx": {"zh-TW": "#", "en": "#"},
    "col_size": {"zh-TW": "大小", "en": "Size"},

    # ---- 變數頁 ----
    "select_item": {"zh-TW": "← 請選擇左側項目以查看詳細資訊", "en": "← Select an item to view details"},
    "sig_type": {"zh-TW": "簽章類型", "en": "Signature Type"},
    "type_guid": {"zh-TW": "類型 GUID", "en": "Type GUID"},
    "owner": {"zh-TW": "Owner", "en": "Owner"},
    "data_size": {"zh-TW": "資料大小", "en": "Data Size"},
    "cert_info": {"zh-TW": "═══ X.509 憑證資訊 ═══", "en": "═══ X.509 Certificate Info ═══"},
    "hash_value": {"zh-TW": "═══ 雜湊值 ═══", "en": "═══ Hash Value ═══"},
    "raw_data": {"zh-TW": "═══ 原始資料 (hex dump) ═══", "en": "═══ Raw Data (hex dump) ═══"},
    "error_read": {"zh-TW": "❌ 讀取錯誤: {}", "en": "❌ Read Error: {}"},
    "no_data": {"zh-TW": "(此變數無資料)", "en": "(No data for this variable)"},

    # ---- 日誌頁 ----
    "log_title": {"zh-TW": "📜 操作日誌", "en": "📜 Operation Log"},

    # ---- 設定頁 ----
    "settings_title": {"zh-TW": "⚙️ 設定", "en": "⚙️ Settings"},
    "ui_theme": {"zh-TW": "UI 介面風格", "en": "UI Theme"},
    "theme_dark": {"zh-TW": "🌙 暗色系", "en": "🌙 Dark"},
    "theme_light": {"zh-TW": "☀️ 亮色系", "en": "☀️ Light"},
    "theme_system": {"zh-TW": "🖥️ 系統設定", "en": "🖥️ System"},
    "language": {"zh-TW": "UI 語言", "en": "UI Language"},
    "copyright": {"zh-TW": "版權資訊", "en": "Copyright"},
    "copyright_text": {"zh-TW": "© 2026 輝寶 (Hui Bao) for 熊哥\nSecure Boot Key Viewer\nAll rights reserved.",
                        "en": "© 2026 Hui Bao for Brother Bear\nSecure Boot Key Viewer\nAll rights reserved."},
    "restart_hint": {"zh-TW": "（切換後立即生效）", "en": "(Takes effect immediately)"},

    # ---- 匯出 ----
    "export_title": {"zh-TW": "匯出 Secure Boot 報告", "en": "Export Secure Boot Report"},
    "html_report": {"zh-TW": "HTML 報告", "en": "HTML Report"},
    "txt_report": {"zh-TW": "文字報告", "en": "Text Report"},
    "all_files": {"zh-TW": "所有檔案", "en": "All Files"},
    "export_success": {"zh-TW": "匯出成功", "en": "Export Successful"},
    "export_saved": {"zh-TW": "報告已儲存至:", "en": "Report saved to:"},
    "export_fail": {"zh-TW": "匯出失敗", "en": "Export Failed"},

    # ---- 對話框 ----
    "admin_needed": {"zh-TW": "需要管理員權限", "en": "Admin Privileges Required"},
    "admin_msg": {"zh-TW": "讀取 UEFI Secure Boot 變數需要系統管理員權限。\n請以「以系統管理員身分執行」重新啟動本程式。",
                   "en": "Reading UEFI Secure Boot variables requires administrator privileges.\nPlease restart as administrator."},
}


def t(key, lang="zh-TW"):
    """取得翻譯字串。

    Args:
        key: 字串 key
        lang: 語言代碼 ('zh-TW' 或 'en')

    Returns:
        str: 翻譯後的字串，找不到時回傳 key 本身
    """
    entry = STRINGS.get(key)
    if not entry:
        return key
    return entry.get(lang, entry.get("zh-TW", key))
