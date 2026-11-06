# Change List

## v00.00.1b

- 修復個別變數頁面 Treeview 白底問題，統一黑色系主題
- 新增 TXT 純文字報告匯出（HTML + TXT 雙格式）
- 左側邊欄底部新增「設定」入口
- 設定頁面：UI 介面風格切換（暗色系 / 亮色系 / 系統設定）
- 設定頁面：UI 語言切換（繁體中文 / English）
- 設定頁面：版權資訊
- 重構主題系統（sbkv/themes.py）：Dark / Light / System 三種主題
- 重構多語系系統（sbkv/i18n.py）：zh-TW / en 雙語切換
- 報告匯出支援多語系（依 UI 語言輸出）
- 詳見 changelogs/v00.00.1b.md

## v00.00.1a

初版（Initial release）。

- 建立專案骨架：main.py + sbkv 套件（collectors / parsers / certs / report / ui / version）
- UEFI Secure Boot 變數讀取：PK、KEK、db、dbx（Win32 API + PowerShell 雙重備援）
- EFI Signature List 結構解析：簽章類型、Owner GUID、簽章資料
- X.509 憑證解析：Subject、Issuer、Serial、有效期限、Thumbprint
- 雜湊值顯示：SHA-1 / SHA-256 / SHA-384 / SHA-512
- Secure Boot 狀態檢測（登錄檔 + Confirm-SecureBootUEFI）
- Tkinter UI：GitHub Dark 設計系統（VVT 風格）
- 報告匯出：Markdown + HTML
- 測試：tests/test_parsers.py（14 項）
- 版號機制：v00.00.1a 起算
