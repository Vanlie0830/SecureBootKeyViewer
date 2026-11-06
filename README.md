# 🔐 Secure Boot Key Viewer

> UEFI Secure Boot PK / KEK / db / dbx 金鑰檢視器 — by 輝寶 for 熊哥

## 簡介

Secure Boot Key Viewer 是一款 Windows 應用程式，用於讀取並顯示 UEFI Secure Boot 的
四個關鍵金鑰/資料庫變數：

| 變數 | 全名 | 說明 |
|------|------|------|
| **PK** | Platform Key | 平台金鑰 — Secure Boot 根信任金鑰 |
| **KEK** | Key Exchange Key | 金鑰交換金鑰 — 簽署 db/dbx 更新 |
| **db** | Signature Database | 簽章資料庫 — 受信任的簽章憑證與雜湊 |
| **dbx** | Forbidden Signature DB | 撤銷簽章資料庫 — 被禁止的簽章 |

## 功能

- 🔑 讀取 PK、KEK、db、dbx 變數（Win32 API + PowerShell 雙重備援）
- 📜 解析 EFI Signature List 結構
- 🏛 X.509 憑證詳情：Subject、Issuer、有效期限、Thumbprint
- 🔏 雜湊值顯示：SHA-1 / SHA-256 / SHA-384 / SHA-512
- 🔒 Secure Boot 狀態檢測
- 🎨 GitHub Dark 設計系統 UI
- 📊 報告匯出：Markdown + HTML

## 系統需求

- Windows 10 / 11 (UEFI 韌體)
- Python 3.10+ (含 tkinter)
- **系統管理員權限** (讀取 UEFI 變數所需)

## 使用方式

```bash
# 啟動 GUI
python main.py

# 顯示版號
python main.py --version

# 自我測試
python main.py --selftest

# 示範模式
python main.py --mock
```

## 測試

```bash
python tests/test_parsers.py
```

## 專案結構

```
SecureBootKeyViewer/
├── main.py              # 入口點
├── sbkv/                # 主套件
│   ├── version.py       # 版號管理
│   ├── collectors.py    # UEFI 變數讀取
│   ├── parsers.py       # EFI Signature List 解析
│   ├── certs.py         # X.509 憑證解析
│   ├── report.py        # 報告匯出
│   └── ui.py            # Tkinter GUI
├── tests/
│   └── test_parsers.py  # 解析器測試
├── changelogs/          # 版本變更記錄
├── CHANGELOG.md
├── VERSION
└── README.md
```

## 版號規則

依熊哥指定：`v00.00.1a` → `v00.00.1b` → ... → `v00.00.1z` → `v00.00.2a`

## 授權

MIT License
