# Change List

## v00.00.1c

- 修復導覽圖示重複問題 (日誌/設定顯示兩個 icon)
- 設計全新應用程式 icon (盾牌 + 鑰匙孔 + 驗證勾勾 + SBK)
- 憑證長文字換行自動對齊 (textwrap + subsequent_indent)
- 詳見 changelogs/v00.00.1c.md

## v00.00.1b

- 修復個別變數頁面 Treeview 白底問題，統一黑色系主題
- 新增 TXT 純文字報告匯出（HTML + TXT 雙格式）
- 左側邊欄底部新增「設定」入口
- 設定頁面：UI 介面風格切換（暗色系 / 亮色系 / 系統設定）
- 設定頁面：UI 語言切換（繁體中文 / English）
- 設定頁面：版權資訊
- 重構主題系統（sbkv/themes.py）：Dark / Light / System
- 重構多語系系統（sbkv/i18n.py）：zh-TW / en

## v00.00.1a

初版（Initial release）。

- 建立專案骨架：main.py + sbkv 套件
- UEFI Secure Boot 變數讀取：PK、KEK、db、dbx
- EFI Signature List 結構解析
- X.509 憑證解析
- Tkinter UI：GitHub Dark 設計系統
- 報告匯出：Markdown + HTML
- 測試：14 項
