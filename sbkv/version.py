"""版號管理。

版號規則（依熊哥指定）：
    v00.00.1a -> v00.00.1b -> ... -> v00.00.1z -> v00.00.2a
即：前段為 vAA.BB.C，尾碼為小寫英文字母；字母用完 (z) 後
第三段數字 +1 並回到 'a'。
"""

import re

VERSION = "v00.00.1d"

_VER_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)([a-z])$")


def parse(version):
    """解析版號為 (a, b, c, letter)。格式錯誤時拋 ValueError。"""
    m = _VER_RE.match(version)
    if not m:
        raise ValueError(f"版號格式錯誤: {version!r}（應為 v00.00.1a 形式）")
    a, b, c, letter = m.groups()
    return int(a), int(b), int(c), letter


def next_version(version):
    """回傳下一個版號。z 之後進位：v00.00.1z -> v00.00.2a。"""
    a, b, c, letter = parse(version)
    if letter == "z":
        return f"v{a:02d}.{b:02d}.{c + 1}a"
    return f"v{a:02d}.{b:02d}.{c}{chr(ord(letter) + 1)}"


def validate(version):
    """版號格式正確回傳 True。"""
    try:
        parse(version)
        return True
    except ValueError:
        return False
