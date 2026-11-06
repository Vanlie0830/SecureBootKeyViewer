"""UI 主題色彩定義。

支援三種主題模式:
    dark   — 暗色系 (GitHub Dark)
    light  — 亮色系 (GitHub Light)
    system — 跟隨系統設定 (偵測 Windows 應用程式主題)
"""

import sys

# ---- GitHub Dark 設計系統 ----
DARK = {
    "bg": "#0d1117",
    "bg2": "#161b22",
    "bg3": "#21262d",
    "card": "#1c2128",
    "border": "#30363d",
    "text": "#e6edf3",
    "text2": "#8b949e",
    "muted": "#6e7681",
    "accent": "#58a6ff",
    "accent2": "#79c0ff",
    "success": "#3fb950",
    "warning": "#d29922",
    "danger": "#f85149",
    "btn_primary": "#1f6feb",
    "btn_primary_hover": "#388bfd",
    "entry_bg": "#0d1117",
    "tree_bg": "#0d1117",
    "tree_field": "#0d1117",
    "tree_heading_bg": "#21262d",
    "tree_heading_fg": "#8b949e",
    "tree_selected": "#1f6feb",
    "tree_selected_fg": "#ffffff",
    "scrollbar_bg": "#30363d",
    "scrollbar_trough": "#161b22",
}

# ---- GitHub Light 設計系統 ----
LIGHT = {
    "bg": "#ffffff",
    "bg2": "#f6f8fa",
    "bg3": "#eaeef2",
    "card": "#ffffff",
    "border": "#d0d7de",
    "text": "#1f2328",
    "text2": "#656d76",
    "muted": "#8c959f",
    "accent": "#0969da",
    "accent2": "#0550ae",
    "success": "#1a7f37",
    "warning": "#9a6700",
    "danger": "#cf222e",
    "btn_primary": "#0969da",
    "btn_primary_hover": "#0550ae",
    "entry_bg": "#ffffff",
    "tree_bg": "#ffffff",
    "tree_field": "#ffffff",
    "tree_heading_bg": "#eaeef2",
    "tree_heading_fg": "#656d76",
    "tree_selected": "#0969da",
    "tree_selected_fg": "#ffffff",
    "scrollbar_bg": "#d0d7de",
    "scrollbar_trough": "#f6f8fa",
}

THEMES = {"dark": DARK, "light": LIGHT}


def get_system_theme():
    """偵測 Windows 系統應用程式主題偏好。

    回傳 'dark' 或 'light'。
    """
    if sys.platform != "win32":
        return "dark"
    try:
        import winreg
        k = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        v, _ = winreg.QueryValueEx(k, "AppsUseLightTheme")
        winreg.CloseKey(k)
        return "light" if v else "dark"
    except Exception:
        return "dark"


def resolve_theme(mode):
    """將主題模式轉換為實際色彩 dict。

    Args:
        mode: 'dark', 'light', 或 'system'

    Returns:
        dict: 色彩 tokens
    """
    if mode == "system":
        mode = get_system_theme()
    return THEMES.get(mode, DARK)
