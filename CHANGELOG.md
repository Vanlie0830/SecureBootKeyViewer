# Change List

## v00.00.1a

初版（Initial release）。

- 建立專案骨架：main.py + sbkv 套件（collectors / parsers / certs / report / ui / version）
- UEFI Secure Boot 變數讀取：PK、KEK、db、dbx（Win32 API + PowerShell 雙重備援）
- EFI Signature List 結構解析：簽章類型、Owner GUID、簽章資料
- X.509 憑證解析：Subject、Issuer、Serial、有效期限、Thumbprint（cryptography / PowerShell .NET 備援）
- 雜湊值顯示：SHA-1 / SHA-256 / SHA-384 / SHA-512
- Secure Boot 狀態檢測（登錄檔 + Confirm-SecureBootUEFI）
- Tkinter UI：GitHub Dark 設計系統（VVT 風格），左側導覽側邊欄 + 指標卡片 + 簽章列表 + 詳細面板
- 報告匯出：Markdown + HTML（GitHub Dark 主題）
- 測試：tests/test_parsers.py（版號、GUID、Signature List、Hex Dump，共 14 項）
- 版號機制：v00.00.1a 起算，尾碼字母遞增
- git 版本控制：專案以 git 管理
