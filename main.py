#!/usr/bin/env python3
"""Secure Boot Key Viewer — 入口點。

用法:
    python main.py            # 啟動 GUI
    python main.py --version  # 顯示版號
    python main.py --mock     # 示範模式 (不需要 UEFI 權限)
"""

import os
import sys

# 確保套件路徑正確 (支援 PyInstaller 打包)
if getattr(sys, "frozen", False):
    _base = os.path.dirname(sys.executable)
else:
    _base = os.path.dirname(os.path.abspath(__file__))
if _base not in sys.path:
    sys.path.insert(0, _base)

from sbkv.version import VERSION  # noqa: E402


def main():
    """主程式入口。"""
    args = sys.argv[1:]

    # --version: 顯示版號後離開
    if "--version" in args:
        print(f"{VERSION}")
        return 0

    # --selftest: 執行自我測試
    if "--selftest" in args:
        return _selftest()

    # 啟動 GUI
    use_mock = "--mock" in args

    # 無主控台模式 (PyInstaller windowed) 重新導向輸出
    if getattr(sys, "frozen", False) and not sys.stdout:
        log_path = os.path.join(_base, "sbkv.log")
        sys.stdout = open(log_path, "w", encoding="utf-8")
        sys.stderr = sys.stdout

    try:
        from sbkv.ui import App
        app = App(use_mock=use_mock)
        app.mainloop()
    except Exception as e:
        # 頂層例外防護: 記錄錯誤後再拋出
        print(f"[FATAL] {e}", file=sys.stderr)
        raise

    return 0


def _selftest():
    """內部自我測試 (不需要 UEFI 權限)。"""
    from sbkv.version import next_version, parse, validate

    print(f"Secure Boot Key Viewer {VERSION} — 自我測試")
    print("=" * 50)

    ok = True

    # 版號格式
    assert validate(VERSION), "版號格式驗證失敗"
    assert validate(next_version(VERSION)), "下一個版號格式驗證失敗"
    print("  ✅ 版號管理")

    # EFI GUID 解析
    from sbkv.parsers import bytes_to_guid
    test_guid = bytes.fromhex("61dfe48bca93d211aa0d00e098032b8c")
    assert bytes_to_guid(test_guid) == "8be4df61-93ca-11d2-aa0d-00e098032b8c", \
        "GUID 解析失敗"
    print("  ✅ EFI GUID 解析")

    # EFI Signature List 解析 (空資料)
    from sbkv.parsers import parse_signature_list
    assert parse_signature_list(b"") == [], "空資料應回傳空列表"
    print("  ✅ EFI Signature List 解析")

    # 憑證解析 (fallback)
    from sbkv.certs import parse_certificate
    dummy = b"\x30\x82\x01\x00" + b"\x00" * 256
    r = parse_certificate(dummy)
    assert "Thumbprint" in r, "憑證解析應回傳 Thumbprint"
    print("  ✅ X.509 憑證解析")

    print("=" * 50)
    print("  全部通過 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
