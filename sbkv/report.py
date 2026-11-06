"""報告匯出模組。

將 Secure Boot 金鑰資訊匯出為 Markdown 或 HTML 報告。
"""

import os
from datetime import datetime

from .certs import parse_certificate
from .collectors import VARIABLES, VAR_ORDER, get_secure_boot_status
from .parsers import HASH_TYPES, hex_dump
from .version import VERSION

APP_NAME = "Secure Boot Key Viewer"


def export_markdown(filepath, results):
    """匯出 Markdown 報告。

    Args:
        filepath: str, 輸出檔案路徑
        results: dict, {var_name: {"entries": [...], "error": str|None}}
    """
    sb = get_secure_boot_status()
    sb_str = "已啟用" if sb else ("未啟用" if sb is False else "無法確定")

    lines = [
        f"# {APP_NAME} {VERSION} — Secure Boot 報告",
        "",
        f"**產生時間:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Secure Boot 狀態:** {sb_str}",
        "",
        "---",
        "",
    ]

    for vname in VAR_ORDER:
        meta = VARIABLES[vname]
        info = results.get(vname, {})
        entries = info.get("entries", [])
        error = info.get("error")

        lines.append(f"## {meta['label']}")
        lines.append(f"*{meta['desc']}*")
        lines.append("")

        if error:
            lines.append(f"> ❌ 讀取錯誤: {error}")
            lines.append("")
            continue

        if not entries:
            lines.append("> (無資料)")
            lines.append("")
            continue

        lines.append(f"共 **{len(entries)}** 筆簽章:")
        lines.append("")

        for i, e in enumerate(entries, 1):
            lines.append(f"### [{i}] {e['type_name']}")
            lines.append("")
            lines.append(f"- **類型 GUID:** `{e['type_guid']}`")
            lines.append(f"- **Owner GUID:** `{e['owner_guid']}`")
            lines.append(f"- **資料大小:** {e['data_size']} bytes")

            if "X.509" in e["type_name"]:
                cert = parse_certificate(e["data"])
                lines.append("")
                lines.append("| 欄位 | 內容 |")
                lines.append("|------|------|")
                for k, v in cert.items():
                    lines.append(f"| {k} | {v} |")
            elif e["type_name"] in HASH_TYPES:
                lines.append(f"- **雜湊值:** `{e['data'].hex().upper()}`")

            lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def export_html(filepath, results):
    """匯出 HTML 報告 (GitHub Dark 風格)。

    Args:
        filepath: str, 輸出檔案路徑
        results: dict, {var_name: {"entries": [...], "error": str|None}}
    """
    sb = get_secure_boot_status()
    sb_str = "已啟用" if sb else ("未啟用" if sb is False else "無法確定")
    sb_color = "#3fb950" if sb else ("#f85149" if sb is False else "#d29922")

    sections = []
    for vname in VAR_ORDER:
        meta = VARIABLES[vname]
        info = results.get(vname, {})
        entries = info.get("entries", [])
        error = info.get("error")

        rows = []
        if error:
            rows.append(
                f'<tr><td colspan="4" style="color:#f85149">讀取錯誤: {error}</td></tr>'
            )
        elif not entries:
            rows.append('<tr><td colspan="4" style="color:#8b949e">(無資料)</td></tr>')
        else:
            for i, e in enumerate(entries, 1):
                detail = ""
                if "X.509" in e["type_name"]:
                    cert = parse_certificate(e["data"])
                    detail = (
                        f"<b>Subject:</b> {cert.get('Subject', '-')}<br>"
                        f"<b>Issuer:</b> {cert.get('Issuer', '-')}<br>"
                        f"<b>Valid:</b> {cert.get('NotBefore', '-')} ~ "
                        f"{cert.get('NotAfter', '-')}<br>"
                        f"<b>Thumbprint:</b> <code>{cert.get('Thumbprint', '-')}</code>"
                    )
                elif e["type_name"] in HASH_TYPES:
                    detail = f"<code>{e['data'].hex().upper()}</code>"

                rows.append(
                    f"<tr>"
                    f"<td>{i}</td>"
                    f"<td>{e['type_name']}</td>"
                    f"<td>{e['data_size']} B</td>"
                    f"<td>{detail}</td>"
                    f"</tr>"
                )

        sections.append(f"""
        <div class="section">
          <h2>{meta['label']}</h2>
          <p class="desc">{meta['desc']}</p>
          <table>
            <thead><tr><th>#</th><th>類型</th><th>大小</th><th>詳細</th></tr></thead>
            <tbody>{''.join(rows)}</tbody>
          </table>
        </div>""")

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>{APP_NAME} {VERSION} — Secure Boot 報告</title>
<style>
  body {{ background:#0d1117; color:#e6edf3; font-family:'Segoe UI',sans-serif;
         margin:0; padding:24px; }}
  h1 {{ color:#58a6ff; }}
  .meta {{ color:#8b949e; margin-bottom:24px; }}
  .meta b {{ color:#e6edf3; }}
  .sb-badge {{ display:inline-block; padding:4px 12px; border-radius:12px;
               background:{sb_color}22; color:{sb_color}; font-weight:bold; }}
  .section {{ background:#161b22; border:1px solid #30363d; border-radius:8px;
              padding:20px; margin-bottom:16px; }}
  .section h2 {{ color:#58a6ff; margin-top:0; }}
  .desc {{ color:#8b949e; font-size:13px; }}
  table {{ width:100%; border-collapse:collapse; margin-top:12px; }}
  th {{ background:#21262d; color:#8b949e; text-align:left; padding:8px 12px;
       font-size:12px; text-transform:uppercase; }}
  td {{ padding:8px 12px; border-top:1px solid #30363d; font-size:13px; }}
  tr:hover td {{ background:#1c2128; }}
  code {{ background:#21262d; padding:2px 6px; border-radius:4px;
          font-family:'Cascadia Code',monospace; font-size:12px; }}
</style>
</head>
<body>
  <h1>🔐 {APP_NAME} {VERSION}</h1>
  <div class="meta">
    <b>產生時間:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
    <b>Secure Boot 狀態:</b> <span class="sb-badge">{sb_str}</span>
  </div>
  {''.join(sections)}
</body>
</html>"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
