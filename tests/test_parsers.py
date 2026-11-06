"""測試 EFI Signature List 解析器與版號管理。"""

import os
import sys
import struct

# 確保可匯入 sbkv 套件
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sbkv.parsers import bytes_to_guid, parse_signature_list, hex_dump
from sbkv.version import VERSION, next_version, parse, validate


class TestVersion:
    """版號管理測試。"""

    def test_format(self):
        assert validate(VERSION)

    def test_parse(self):
        a, b, c, letter = parse("v00.00.1a")
        assert (a, b, c, letter) == (0, 0, 1, "a")

    def test_next_version_letter(self):
        assert next_version("v00.00.1a") == "v00.00.1b"

    def test_next_version_carry(self):
        assert next_version("v00.00.1z") == "v00.00.2a"

    def test_invalid(self):
        assert not validate("v0.0.1")
        assert not validate("abc")


class TestGuid:
    """EFI GUID 解析測試。"""

    def test_known_guid(self):
        # 8BE4DF61-93CA-11D2-AA0D-00E098032B8C (EFI_GLOBAL_VARIABLE)
        raw = bytes.fromhex("61dfe48bca93d211aa0d00e098032b8c")
        assert bytes_to_guid(raw) == "8be4df61-93ca-11d2-aa0d-00e098032b8c"

    def test_short_input(self):
        assert bytes_to_guid(b"\x00") == ""


class TestSignatureList:
    """EFI Signature List 解析測試。"""

    @staticmethod
    def _guid_str_to_bytes(guid_str):
        """將 GUID 字串 "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        轉換為 EFI little-endian 二進位格式 (16 bytes)。"""
        parts = guid_str.replace("-", "")
        d1 = int(parts[0:8], 16)
        d2 = int(parts[8:12], 16)
        d3 = int(parts[12:16], 16)
        d4 = bytes.fromhex(parts[16:20])
        d5 = bytes.fromhex(parts[20:32])
        return struct.pack("<IHH", d1, d2, d3) + d4 + d5

    def _make_sig_list(self, sig_type_guid_str, signatures):
        """建立 EFI_SIGNATURE_LIST 測試資料。

        Args:
            sig_type_guid_str: str, GUID 字串格式
            signatures: list[bytes], 每筆簽章資料 (不含 Owner GUID)
        """
        owner = b"\x01" * 16  # Owner GUID (任意)
        sig_size = 16 + len(signatures[0]) if signatures else 16

        # 每筆 EFI_SIGNATURE_DATA: owner (16) + data
        sig_data = b""
        for s in signatures:
            sig_data += owner + s

        header_size = 0
        list_size = 28 + header_size + len(sig_data)

        header = struct.pack(
            "<16sIII",
            self._guid_str_to_bytes(sig_type_guid_str),
            list_size,
            header_size,
            sig_size,
        )
        return header + sig_data

    def test_empty(self):
        assert parse_signature_list(b"") == []

    def test_single_sha256(self):
        # SHA-256 GUID
        guid = "c1c41626-504c-4092-aca9-41f936934328"
        hash_val = b"\xab" * 32
        data = self._make_sig_list(guid, [hash_val])
        entries = parse_signature_list(data)

        assert len(entries) == 1
        assert entries[0]["type_name"] == "SHA-256 Hash"
        assert entries[0]["data"] == hash_val
        assert entries[0]["data_size"] == 32

    def test_multiple_entries(self):
        guid = "c1c41626-504c-4092-aca9-41f936934328"
        hashes = [b"\xaa" * 32, b"\xbb" * 32, b"\xcc" * 32]
        data = self._make_sig_list(guid, hashes)
        entries = parse_signature_list(data)

        assert len(entries) == 3
        assert entries[0]["data"] == hashes[0]
        assert entries[1]["data"] == hashes[1]
        assert entries[2]["data"] == hashes[2]

    def test_two_lists(self):
        """兩個不同類型的 Signature List 串接。"""
        guid_256 = "c1c41626-504c-4092-aca9-41f936934328"
        guid_512 = "093e0fa6-5d61-4a38-8a59-4d6c6c1e5a58"
        data = (
            self._make_sig_list(guid_256, [b"\xaa" * 32])
            + self._make_sig_list(guid_512, [b"\xbb" * 64])
        )
        entries = parse_signature_list(data)

        assert len(entries) == 2
        assert entries[0]["type_name"] == "SHA-256 Hash"
        assert entries[1]["type_name"] == "SHA-512 Hash"

    def test_x509_type(self):
        guid_x509 = "a5c059a1-94e4-4aa7-87b5-ab155c2bf072"
        dummy_cert = b"\x30\x82\x01\x00" + b"\x00" * 252
        data = self._make_sig_list(guid_x509, [dummy_cert])
        entries = parse_signature_list(data)

        assert len(entries) == 1
        assert entries[0]["type_name"] == "X.509 Certificate"


class TestHexDump:
    """Hex dump 測試。"""

    def test_basic(self):
        result = hex_dump(b"\x00\x01\x02")
        assert "000102" in result.replace(" ", "")

    def test_empty(self):
        assert hex_dump(b"") == ""


# ---- 命令列執行入口 ----

if __name__ == "__main__":
    import traceback

    passed = 0
    failed = 0

    for cls_name in ["TestVersion", "TestGuid", "TestSignatureList", "TestHexDump"]:
        cls = globals()[cls_name]
        instance = cls()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    getattr(instance, method_name)()
                    passed += 1
                    print(f"  ✅ {cls_name}.{method_name}")
                except Exception:
                    failed += 1
                    print(f"  ❌ {cls_name}.{method_name}")
                    traceback.print_exc()

    print(f"\n結果: {passed} 通過, {failed} 失敗")
    sys.exit(1 if failed else 0)
