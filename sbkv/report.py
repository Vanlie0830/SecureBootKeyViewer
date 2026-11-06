"""報告匯出模組。

支援三種格式匯出:
    .html — GitHub Dark 主題 HTML 報告
    .md   — Markdown 報告
    .txt  — 純文字報告 (v00.00.1b 新增)
"""

from datetime import datetime

from .certs import parse_certificate
from .collectors import VARIABLES, VAR_ORDER, get_secure_boot_status
from .parsers import HASH_TYPES
from .version import VERSION

APP_NAME = "Secure Boot Key Viewer"


def _sb_str(lang):
    """取得 Secure Boot 狀態字串與布林值。"""
    from .i18n import t
    sb = get_secure_boot_status()
    if sb is True:
        return t("enabled", lang), True
    if sb is False:
        return t("disabled", lang), False
    return t("unknown", lang), None


# ---- Markdown ----

def export_markdown(filepath, results, lang="zh-TW"):
    """匯出 Markdown 報告。"""
    from .i18n import t
    sb_str, _ = _sb_str(lang)
    lines = [
        f"# {APP_NAME} {VERSION} \u2014 Secure Boot Report",
        "",
        f"**{t('export_title', lang)}:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**{t('sb_status', lang)}:** {sb_str}",
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
            lines.append(f"> ERROR: {error}")
            lines.append("")
            continue
        if not entries:
            lines.append(f"> {t('no_data', lang)}")
            lines.append("")
            continue
        for i, e in enumerate(entries, 1):
            lines.append(f"### [{i}] {e['type_name']}")
            lines.append("")
            lines.append(f"- **Type GUID:** `{e['type_guid']}`")
            lines.append(f"- **Owner GUID:** `{e['owner_guid']}`")
            lines.append(f"- **Size:** {e['data_size']} bytes")
            if "X.509" in e["type_name"]:
                cert = parse_certificate(e["data"])
                lines.append("")
                lines.append("| Field | Value |")
                lines.append("|-------|-------|")
                for k, v in cert.items():
                    lines.append(f"| {k} | {v} |")
            elif e["type_name"] in HASH_TYPES:
                lines.append(f"- **Hash:** `{e['data'].hex().upper()}`")
            lines.append("")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---- Text (v00.00.1b) ----

def export_text(filepath, results, lang="zh-TW"):
    """匯出純文字 (.txt) 報告。"""
    from .i18n import t
    sb_str, _ = _sb_str(lang)
    sep = "=" * 60
    sub = "-" * 60
    lines = [
        sep,
        f"  {APP_NAME} {VERSION}",
        "  Secure Boot Report",
        sep,
        "",
        f"  {t('export_title', lang)}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"  {t('sb_status', lang)}: {sb_str}",
        "",
    ]
    for vname in VAR_ORDER:
        meta = VARIABLES[vname]
        info = results.get(vname, {})
        entries = info.get("entries", [])
        error = info.get("error")
        lines.append(sub)
        lines.append(f"  {meta['label']}")
        lines.append(f"  {meta['desc']}")
        lines.append(sub)
        lines.append("")
        if error:
            lines.append(f"  ERROR: {error}")
            lines.append("")
            continue
        if not entries:
            lines.append(f"  {t('no_data', lang)}")
            lines.append("")
            continue
        lines.append(f"  Total: {len(entries)} entries")
        lines.append("")
        for i, e in enumerate(entries, 1):
            lines.append(f"  [{i}] {e['type_name']}")
            lines.append(f"      Type GUID:  {e['type_guid']}")
            lines.append(f"      Owner GUID: {e['owner_guid']}")
            lines.append(f"      Data Size:  {e['data_size']} bytes")
            if "X.509" in e["type_name"]:
                cert = parse_certificate(e["data"])
                lines.append("")
                lines.append(f"      --- {t('cert_info', lang)} ---")
                for k, v in cert.items():
                    lines.append(f"      {k:16s} {v}")
            elif e["type_name"] in HASH_TYPES:
                lines.append(f"      Hash: {e['data'].hex().upper()}")
            lines.append("")
    lines.append(sep)
    copyright_text = t("copyright_text", lang).replace("\n", "\n  ")
    lines.append(f"  {copyright_text}")
    lines.append(sep)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---- HTML ----

def export_html(filepath, results, lang="zh-TW"):
    """匯出 HTML 報告 (GitHub Dark)。"""
    from .i18n import t
    from .themes import DARK as C
    sb_str, sb = _sb_str(lang)
    sb_color = C["success"] if sb else (C["danger"] if sb is False else C["warning"])
    sections = []
    for vname in VAR_ORDER:
        meta = VARIABLES[vname]
        info = results.get(vname, {})
        entries = info.get("entries", [])
        error = info.get("error")
        rows = []
        if error:
            rows.append(f'<tr><td colspan="4" style="color:{C["danger"]}">ERROR: {error}</td></tr>')
        elif not entries:
            rows.append(f'<tr><td colspan="4" style="color:{C["muted"]}">{t("no_data", lang)}</td></tr>')
        else:
            for i, e in enumerate(entries, 1):
                detail = ""
                if "X.509" in e["type_name"]:
                    cert = parse_certificate(e["data"])
                    detail = (
                        f"<b>Subject:</b> {cert.get('Subject', '-')}<br>"
                        f"<b>Issuer:</b> {cert.get('Issuer', '-')}<br>"
                        f"<b>Valid:</b> {cert.get('NotBefore', '-')} ~ {cert.get('NotAfter', '-')}<br>"
                        f"<b>Thumbprint:</b> <code>{cert.get('Thumbprint', '-')}</code>"
                    )
                elif e["type_name"] in HASH_TYPES:
                    detail = f"<code>{e['data'].hex().upper()}</code>"
                rows.append(f"<tr><td>{i}</td><td>{e['type_name']}</td><td>{e['data_size']} B</td><td>{detail}</td></tr>")
        sections.append(f'<div class="section"><h2>{meta["label"]}</h2><p class="desc">{meta["desc"]}</p><table><thead><tr><th>#</th><th>{t("col_type", lang)}</th><th>{t("col_size", lang)}</th><th>Detail</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
    copyright_html = t("copyright_text", lang).replace("\n", "<br>")
    html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<title>{APP_NAME} {VERSION} - Secure Boot Report</title>
<style>
  body {{ background:{C['bg']}; color:{C['text']}; font-family:'Segoe UI',sans-serif; margin:0; padding:24px; }}
  h1 {{ color:{C['accent']}; }}
  .meta {{ color:{C['text2']}; margin-bottom:24px; }}
  .sb-badge {{ display:inline-block; padding:4px 12px; border-radius:12px; background:{sb_color}22; color:{sb_color}; font-weight:bold; }}
  .section {{ background:{C['bg2']}; border:1px solid {C['border']}; border-radius:8px; padding:20px; margin-bottom:16px; }}
  .section h2 {{ color:{C['accent']}; margin-top:0; }}
  .desc {{ color:{C['text2']}; font-size:13px; }}
  table {{ width:100%; border-collapse:collapse; margin-top:12px; }}
  th {{ background:{C['bg3']}; color:{C['text2']}; text-align:left; padding:8px 12px; font-size:12px; text-transform:uppercase; }}
  td {{ padding:8px 12px; border-top:1px solid {C['border']}; font-size:13px; }}
  tr:hover td {{ background:{C['card']}; }}
  code {{ background:{C['bg3']}; padding:2px 6px; border-radius:4px; font-family:'Cascadia Code',monospace; font-size:12px; }}
  .footer {{ margin-top:32px; padding-top:16px; border-top:1px solid {C['border']}; color:{C['muted']}; font-size:12px; }}
</style>
</head>
<body>
  <h1>Secure Boot Key Viewer {VERSION}</h1>
  <div class="meta">
    <b>{t('export_title', lang)}:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
    <b>{t('sb_status', lang)}:</b> <span class="sb-badge">{sb_str}</span>
  </div>
  {''.join(sections)}
  <div class="footer">{copyright_html}</div>
</body>
</html>"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
