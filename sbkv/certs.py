"""X.509 憑證解析。

解析 Secure Boot 變數中的 X.509 DER 編碼憑證，
擷取 Subject、Issuer、有效期限、指紋等資訊。

解析方法優先順序:
    1. cryptography 函式庫 (若已安裝)
    2. PowerShell .NET X509Certificate2
    3. 基本資訊 (SHA-256 指紋)
"""

import base64
import hashlib
import json
import subprocess

# 憑證解析結果快取 (避免重複解析)
_cert_cache = {}


def parse_certificate(der_bytes):
    """解析 X.509 DER 憑證，回傳憑證資訊 dict。

    Args:
        der_bytes: bytes, DER 編碼的 X.509 憑證

    Returns:
        dict: 憑證資訊，包含以下欄位 (若解析失敗則標記 '-'):
            Subject, Issuer, Serial, NotBefore, NotAfter,
            Thumbprint, SigAlg, KeySize
    """
    # 快取檢查
    cache_key = hashlib.sha256(der_bytes).hexdigest()
    if cache_key in _cert_cache:
        return _cert_cache[cache_key]

    # 方法 1: cryptography 函式庫
    result = _parse_with_cryptography(der_bytes)
    if result is not None:
        _cert_cache[cache_key] = result
        return result

    # 方法 2: PowerShell .NET
    result = _parse_with_powershell(der_bytes)
    if result is not None:
        _cert_cache[cache_key] = result
        return result

    # 方法 3: 基本資訊 (只算 SHA-256 指紋)
    result = {
        "Subject": "(無法解析 — 請安裝 cryptography 套件)",
        "Issuer": "-",
        "Serial": "-",
        "NotBefore": "-",
        "NotAfter": "-",
        "Thumbprint": hashlib.sha256(der_bytes).hexdigest().upper(),
        "SigAlg": "-",
        "KeySize": "-",
    }
    _cert_cache[cache_key] = result
    return result


def _parse_with_cryptography(der_bytes):
    """使用 cryptography 函式庫解析憑證。成功回傳 dict，失敗回傳 None。"""
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes

        cert = x509.load_der_x509_certificate(der_bytes)

        # Subject / Issuer (DN 格式)
        subj = ", ".join(f"{a.oid._name}={a.value}" for a in cert.subject)
        iss = ", ".join(f"{a.oid._name}={a.value}" for a in cert.issuer)

        # 公鑰資訊
        pk = cert.public_key()
        try:
            from cryptography.hazmat.primitives.asymmetric import rsa
            if isinstance(pk, rsa.RSAPublicKey):
                key_info = f"RSA-{pk.key_size}"
            else:
                key_info = type(pk).__name__
        except Exception:
            key_info = "-"

        return {
            "Subject": subj,
            "Issuer": iss,
            "Serial": format(cert.serial_number, "x").upper(),
            "NotBefore": cert.not_valid_before_utc.strftime("%Y-%m-%d %H:%M:%S"),
            "NotAfter": cert.not_valid_after_utc.strftime("%Y-%m-%d %H:%M:%S"),
            "Thumbprint": cert.fingerprint(hashes.SHA256()).hex().upper(),
            "SigAlg": cert.signature_algorithm_oid._name,
            "KeySize": key_info,
        }
    except ImportError:
        return None  # cryptography 未安裝
    except Exception:
        return None  # 解析失敗


def _parse_with_powershell(der_bytes):
    """使用 PowerShell .NET X509Certificate2 解析憑證。成功回傳 dict，失敗回傳 None。"""
    b64 = base64.b64encode(der_bytes).decode("ascii")

    ps_cmd = (
        f'$ErrorActionPreference="Stop";'
        f'$b=[Convert]::FromBase64String("{b64}");'
        f'$c=New-Object System.Security.Cryptography.X509Certificates'
        f'.X509Certificate2(,$b);'
        f'$o=[ordered]@{{'
        f'Subject=$c.Subject;'
        f'Issuer=$c.Issuer;'
        f'Serial=$c.SerialNumber;'
        f'NotBefore=$c.NotBefore.ToString("yyyy-MM-dd HH:mm:ss");'
        f'NotAfter=$c.NotAfter.ToString("yyyy-MM-dd HH:mm:ss");'
        f'Thumbprint=$c.Thumbprint;'
        f'SigAlg=$c.SignatureAlgorithm.FriendlyName;'
        f'KeySize="RSA-$($c.PublicKey.Key.KeySize)"'
        f'}};'
        f'$o|ConvertTo-Json'
    )

    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            creationflags=0x08000000,  # CREATE_NO_WINDOW
            timeout=15,
        )
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except Exception:
        pass

    return None
