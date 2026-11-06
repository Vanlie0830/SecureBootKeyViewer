"""EFI Signature List 結構解析。

解析 UEFI 變數中的 EFI_SIGNATURE_LIST 二進位結構，
擷取簽章類型、Owner GUID、以及簽章資料 (X.509 憑證或雜湊值)。

EFI_SIGNATURE_LIST 結構 (UEFI Spec 2.10 §32.4.1):
    EFI_GUID SignatureType        (16 bytes)
    UINT32   SignatureListSize    (4 bytes)
    UINT32   SignatureHeaderSize  (4 bytes)
    UINT32   SignatureSize        (4 bytes)
    UINT8    SignatureHeader[SignatureHeaderSize]
    EFI_SIGNATURE_DATA Signatures[]  (每筆 SignatureSize bytes)

EFI_SIGNATURE_DATA:
    EFI_GUID SignatureOwner       (16 bytes)
    UINT8    SignatureData[]      (SignatureSize - 16 bytes)
"""

import struct

# ---- EFI 簽章類型 GUID → 名稱對照表 ----
SIG_TYPES = {
    "a5c059a1-94e4-4aa7-87b5-ab155c2bf072": "X.509 Certificate",
    "c1c41626-504c-4092-aca9-41f936934328": "SHA-256 Hash",
    "ff3e5307-f38b-4232-8cee-5c74e9dc43e0": "SHA-384 Hash",
    "093e0fa6-5d61-4a38-8a59-4d6c6c1e5a58": "SHA-512 Hash",
    "826ccf55-5930-4e65-8c8c-957a5fc46458": "SHA-1 Hash",
    "3c5766e8-269c-4e34-aa14-ed776e85b3b6": "RSA-2048 Public Key",
    "e81584ce-2538-4bdb-a2c1-e0b6e4d8e8c5": "X.509 Certificate (Win)",
}

# 已知雜湊類型 (用於判斷顯示方式)
HASH_TYPES = {"SHA-256 Hash", "SHA-384 Hash", "SHA-512 Hash", "SHA-1 Hash"}


def bytes_to_guid(b):
    """將 16 bytes 轉換為 EFI GUID 字串格式 (小端序)。

    Args:
        b: bytes, 至少 16 bytes

    Returns:
        str: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" 格式
    """
    if len(b) < 16:
        return ""
    d1, d2, d3 = struct.unpack_from("<IHH", b, 0)
    d4 = b[8:10].hex()
    d5 = b[10:16].hex()
    return f"{d1:08x}-{d2:04x}-{d3:04x}-{d4}-{d5}"


def parse_signature_list(data):
    """解析 EFI_SIGNATURE_LIST 二進位資料。

    Args:
        data: bytes, UEFI 變數原始資料

    Returns:
        list[dict]: 每筆簽章的資訊列表，每筆包含:
            - type_guid: 簽章類型 GUID 字串
            - type_name: 簽章類型名稱 (如 "X.509 Certificate")
            - owner_guid: 簽章擁有者 GUID 字串
            - data: bytes, 簽章原始資料 (不含 Owner GUID)
            - data_size: int, 簽章資料大小 (bytes)
    """
    entries = []
    offset = 0
    total = len(data)

    while offset + 28 <= total:  # EFI_SIGNATURE_LIST header = 28 bytes
        # 解析 header
        sig_type_guid = bytes_to_guid(data[offset:offset + 16])
        list_size = struct.unpack_from("<I", data, offset + 16)[0]
        hdr_size = struct.unpack_from("<I", data, offset + 20)[0]
        sig_size = struct.unpack_from("<I", data, offset + 24)[0]

        # 驗證結構完整性
        if list_size < 28 or offset + list_size > total:
            break

        # 計算簽章資料起訖位置
        sig_start = offset + 28 + hdr_size
        sig_end = offset + list_size

        # 解析每筆簽章 (至少需要 16 bytes for Owner GUID)
        if sig_size >= 16:
            pos = sig_start
            while pos + sig_size <= sig_end:
                owner_guid = bytes_to_guid(data[pos:pos + 16])
                payload = data[pos + 16:pos + sig_size]

                entries.append({
                    "type_guid": sig_type_guid,
                    "type_name": SIG_TYPES.get(
                        sig_type_guid,
                        f"Unknown ({sig_type_guid})",
                    ),
                    "owner_guid": owner_guid,
                    "data": payload,
                    "data_size": len(payload),
                })
                pos += sig_size

        offset += list_size

    return entries


def hex_dump(data, width=16):
    """產生十六進位轉儲 (hex dump) 字串。

    Args:
        data: bytes
        width: int, 每行位元組數 (預設 16)

    Returns:
        str: 格式化的 hex dump
    """
    lines = []
    for i in range(0, len(data), width):
        chunk = data[i:i + width]
        h = " ".join(f"{b:02x}" for b in chunk)
        a = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{i:04x}  {h:<{width * 3}}  {a}")
    return "\n".join(lines)
