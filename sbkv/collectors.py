"""UEFI Secure Boot 變數讀取。

透過 Win32 API (GetFirmwareEnvironmentVariableW) 或
PowerShell (Get-SecureBootUEFI) 讀取 PK、KEK、db、dbx 變數。
需要系統管理員權限。
"""

import base64
import ctypes
import json
import subprocess

# ---- UEFI 變數定義 ----
# PK、KEK 位於 EFI_GLOBAL_VARIABLE 命名空間
# db、dbx 位於 EFI_IMAGE_SECURITY_DATABASE_GUID 命名空間
EFI_GLOBAL_VARIABLE = "{8be4df61-93ca-11d2-aa0d-00e098032b8c}"
EFI_IMAGE_SECURITY_DB = "{d719b2cb-3d3a-4596-a3bc-dad00e67656f}"

VARIABLES = {
    "PK": {
        "label": "Platform Key (PK)",
        "desc": "平台金鑰 — Secure Boot 根信任金鑰",
        "guid": EFI_GLOBAL_VARIABLE,
    },
    "KEK": {
        "label": "Key Exchange Key (KEK)",
        "desc": "金鑰交換金鑰 — 簽署 db/dbx 更新",
        "guid": EFI_GLOBAL_VARIABLE,
    },
    "db": {
        "label": "Signature Database (db)",
        "desc": "簽章資料庫 — 受信任的簽章憑證與雜湊",
        "guid": EFI_IMAGE_SECURITY_DB,
    },
    "dbx": {
        "label": "Forbidden Signature DB (dbx)",
        "desc": "撤銷簽章資料庫 — 被禁止的簽章憑證與雜湊",
        "guid": EFI_IMAGE_SECURITY_DB,
    },
}

VAR_ORDER = ["PK", "KEK", "db", "dbx"]


# ---- 權限偵測 ----

def is_admin():
    """檢查是否以系統管理員身分執行。"""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


# ---- UEFI 變數讀取 ----

def read_uefi_variable(name):
    """讀取指定的 UEFI Secure Boot 變數，回傳原始 bytes。

    優先使用 Win32 API (ctypes)，失敗時改用 PowerShell。
    權限不足或變數不存在時拋 RuntimeError。
    """
    meta = VARIABLES.get(name, {})
    guid = meta.get("guid", EFI_GLOBAL_VARIABLE)

    # 方法 1: Win32 API (速度快)
    try:
        return _read_via_win32(name, guid)
    except Exception:
        pass

    # 方法 2: PowerShell (相容性高)
    return _read_via_powershell(name)


def _read_via_win32(name, guid):
    """透過 GetFirmwareEnvironmentVariableW 讀取 UEFI 變數。"""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    name_buf = ctypes.create_unicode_buffer(name)
    guid_buf = ctypes.create_unicode_buffer(guid)

    # 第一次呼叫取得所需緩衝區大小
    size = kernel32.GetFirmwareEnvironmentVariableW(
        name_buf, guid_buf, None, 0
    )
    if size == 0:
        raise ctypes.WinError(ctypes.get_last_error())

    # 第二次呼叫讀取實際資料
    buf = ctypes.create_string_buffer(size)
    n = kernel32.GetFirmwareEnvironmentVariableW(
        name_buf, guid_buf, buf, size
    )
    if n == 0:
        raise ctypes.WinError(ctypes.get_last_error())

    return buf.raw[:n]


def _read_via_powershell(name):
    """透過 PowerShell Get-SecureBootUEFI 讀取 UEFI 變數。"""
    ps_cmd = (
        f'$ErrorActionPreference="Stop";'
        f'$d=Get-SecureBootUEFI -Name "{name}";'
        f'[Convert]::ToBase64String($d.Bytes)'
    )
    r = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
        capture_output=True,
        text=True,
        creationflags=0x08000000,  # CREATE_NO_WINDOW
        timeout=30,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"PowerShell 讀取 {name} 失敗: {r.stderr.strip()}"
        )
    b64 = r.stdout.strip()
    if not b64:
        raise RuntimeError(f"{name} 變數為空")
    return base64.b64decode(b64)


# ---- Secure Boot 狀態 ----

def get_secure_boot_status():
    """取得 Secure Boot 狀態。

    回傳: True=已啟用, False=未啟用, None=無法確定
    """
    # 方法 1: 登錄檔 (不需要管理員)
    try:
        import winreg
        k = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\SecureBoot\State",
        )
        v, _ = winreg.QueryValueEx(k, "UEFISecureBootEnabled")
        winreg.CloseKey(k)
        return bool(v)
    except Exception:
        pass

    # 方法 2: PowerShell Confirm-SecureBootUEFI
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-Command", "Confirm-SecureBootUEFI"],
            capture_output=True,
            text=True,
            creationflags=0x08000000,
            timeout=10,
        )
        out = r.stdout.strip().lower()
        if out == "true":
            return True
        if out == "false":
            return False
    except Exception:
        pass

    return None


# ---- 批次讀取所有變數 ----

def read_all_variables():
    """讀取所有 Secure Boot 變數 (PK, KEK, db, dbx)。

    回傳 dict: {var_name: {"raw": bytes, "error": str|None}}
    """
    result = {}
    for name in VAR_ORDER:
        try:
            raw = read_uefi_variable(name)
            result[name] = {"raw": raw, "error": None}
        except Exception as e:
            result[name] = {"raw": b"", "error": str(e)}
    return result
