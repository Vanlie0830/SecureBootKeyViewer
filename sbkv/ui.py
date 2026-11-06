"""Tkinter 圖形介面 — GitHub Dark/Light 設計系統 (VVT 風格)。

與 ModernStandbyTester 同一設計語言：
  左側 200px 導覽側邊欄（active：3px 藍色左邊框）、
  頂部動作工具列、底部狀態列、指標卡片、扁平按鈕、
  Segoe UI + Cascadia Code 字體。

v00.00.1b: 新增主題切換(暗/亮/系統)、語言切換(中/英)、設定頁面、TXT匯出
"""

import queue
import textwrap
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import collectors, parsers, report
from .certs import parse_certificate
from .collectors import VARIABLES, VAR_ORDER, get_secure_boot_status, is_admin
from .i18n import t as _t, LANGS
from .parsers import HASH_TYPES
from .themes import resolve_theme
from .version import VERSION

APP_TITLE = "Secure Boot Key Viewer"

FONT_SANS = ("Segoe UI", 10)
FONT_SANS_SM = ("Segoe UI", 9)
FONT_MONO = ("Cascadia Code", 10)
FONT_MONO_SM = ("Cascadia Code", 9)
FONT_H1 = ("Segoe UI", 14, "bold")
FONT_H2 = ("Segoe UI", 12, "bold")
FONT_METRIC = ("Cascadia Code", 18, "bold")


class App(tk.Tk):
    """主視窗。"""

    def __init__(self, use_mock=False):
        super().__init__()
        self.use_mock = use_mock
        self.results = {}
        self.queue = queue.Queue()
        self.busy = False
        self.nav_buttons = {}
        self.nav_bars = {}
        self._current_page = None
        self._sb_status = None

        # 主題與語言設定 (v00.00.1b)
        self.theme_mode = "dark"   # dark / light / system
        self.lang = "zh-TW"        # zh-TW / en

        self._apply_theme()
        self.title(f"{APP_TITLE} {VERSION}")
        self.geometry("1100x740")
        self.minsize(900, 600)

        self._build_all()
        self.after(200, self._start_load)

        if not is_admin():
            self.after(500, lambda: messagebox.showwarning(
                self._t("admin_needed"), self._t("admin_msg")))

    # ---- 主題 / 語言 helpers ----

    def _t(self, key):
        """取得目前語言的翻譯字串。"""
        return _t(key, self.lang)

    def _apply_theme(self):
        """解析目前主題模式並套用色彩。"""
        self.C = resolve_theme(self.theme_mode)
        self.configure(bg=self.C["bg"])
        self._setup_styles()

    def _setup_styles(self):
        """設定 ttk 樣式 (修復 Treeview 白底問題)。"""
        C = self.C
        s = ttk.Style(self)
        s.theme_use("clam")

        # 全域
        s.configure(".", background=C["bg"], foreground=C["text"],
                     borderwidth=0)
        s.configure("TFrame", background=C["bg"])
        s.configure("TLabel", background=C["bg"], foreground=C["text"])
        s.configure("TButton", background=C["bg3"], foreground=C["text"],
                     padding=[10, 5])
        s.map("TButton", background=[("active", C["accent"])])

        # Notebook (未使用但保留)
        s.configure("TNotebook", background=C["bg"], borderwidth=0)
        s.configure("TNotebook.Tab", background=C["bg3"],
                     foreground=C["text"], padding=[12, 6])

        # Treeview — 關鍵：統一深色背景
        s.configure("Treeview",
                     background=C["tree_bg"],
                     fieldbackground=C["tree_field"],
                     foreground=C["text"],
                     borderwidth=0, relief="flat", rowheight=28)
        s.configure("Treeview.Heading",
                     background=C["tree_heading_bg"],
                     foreground=C["tree_heading_fg"],
                     relief="flat", font=("Segoe UI", 9))
        s.map("Treeview",
              background=[("selected", C["tree_selected"])],
              foreground=[("selected", C["tree_selected_fg"])])

        # 捲軸
        s.configure("Vertical.TScrollbar",
                     background=C["scrollbar_bg"],
                     troughcolor=C["scrollbar_trough"],
                     borderwidth=0, relief="flat")
        s.configure("Horizontal.TScrollbar",
                     background=C["scrollbar_bg"],
                     troughcolor=C["scrollbar_trough"],
                     borderwidth=0, relief="flat")

    def _rebuild_ui(self):
        """重建整個 UI (主題或語言切換後呼叫)。"""
        for widget in self.winfo_children():
            widget.destroy()
        self.nav_buttons.clear()
        self.nav_bars.clear()
        self._apply_theme()
        self._build_all()
        if self._current_page:
            self._show_page(self._current_page)

    def _build_all(self):
        """建立整體版面。"""
        self._build_layout()
        self._show_page("overview" if not self._current_page else self._current_page)

    # ---- 版面 ----

    def _build_layout(self):
        C = self.C
        # 側邊欄
        sidebar = tk.Frame(self, bg=C["bg2"], width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="SBK Viewer", bg=C["bg2"],
                 fg=C["accent"], font=FONT_H2, anchor="w",
                 padx=16, pady=16).pack(fill="x")

        nav_items = [
            ("overview", "\U0001f4cb", self._t("nav_overview")),
            ("PK", "\U0001f511", "PK"),
            ("KEK", "\U0001f510", "KEK"),
            ("db", "\u2705", "db"),
            ("dbx", "\U0001f6ab", "dbx"),
            ("log", "\U0001f4dc", self._t("nav_log")),
        ]
        for key, icon, label in nav_items:
            self._make_nav_button(sidebar, key, icon, label)

        # 底部: 設定 + 版號
        self._make_nav_button(sidebar, "settings", "\u2699\ufe0f",
                              self._t("nav_settings"), bottom=True)
        tk.Label(sidebar, text=f"  {VERSION}", bg=C["bg2"],
                 fg=C["muted"], font=FONT_SANS_SM, anchor="w"
                 ).pack(side="bottom", fill="x", pady=8)

        # 主內容
        main = tk.Frame(self, bg=C["bg"])
        main.pack(side="left", fill="both", expand=True)

        # 工具列
        toolbar = tk.Frame(main, bg=C["bg2"], height=48)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        tk.Button(toolbar, text=self._t("btn_refresh"),
                  bg=C["bg3"], fg=C["text"],
                  activebackground=C["accent"], activeforeground=C["bg"],
                  font=FONT_SANS, relief="flat", padx=16, pady=6,
                  command=self._start_load).pack(side="left", padx=(12, 4), pady=8)

        tk.Button(toolbar, text=self._t("btn_export"),
                  bg=C["bg3"], fg=C["text"],
                  activebackground=C["accent"], activeforeground=C["bg"],
                  font=FONT_SANS, relief="flat", padx=16, pady=6,
                  command=self._export_report).pack(side="left", padx=4, pady=8)

        self.sb_label = tk.Label(toolbar, text=self._t("sb_checking"),
                                 bg=C["bg2"], fg=C["text2"], font=FONT_SANS)
        self.sb_label.pack(side="right", padx=16)

        # 頁面容器
        self.page_container = tk.Frame(main, bg=C["bg"])
        self.page_container.pack(fill="both", expand=True, padx=16, pady=12)

        # 狀態列
        self.status_var = tk.StringVar(value=self._t("ready"))
        tk.Label(self, textvariable=self.status_var,
                 bg=C["bg2"], fg=C["text2"], font=FONT_SANS_SM,
                 anchor="w", padx=12, pady=4).pack(side="bottom", fill="x")

    def _make_nav_button(self, parent, key, icon, label, bottom=False):
        C = self.C
        container = tk.Frame(parent, bg=C["bg2"])
        if bottom:
            container.pack(side="bottom", fill="x")
        else:
            container.pack(fill="x")

        bar = tk.Frame(container, bg=C["bg2"], width=3)
        bar.pack(side="left", fill="y")

        btn = tk.Label(container, text=f"  {icon}  {label}",
                       bg=C["bg2"], fg=C["text2"], font=FONT_SANS,
                       anchor="w", padx=12, pady=10, cursor="hand2")
        btn.pack(side="left", fill="x", expand=True)

        def on_click(e=None, k=key):
            self._show_page(k)
        def on_enter(e):
            if self._current_page != key:
                btn.configure(bg=C["bg3"], fg=C["text"])
        def on_leave(e):
            if self._current_page != key:
                btn.configure(bg=C["bg2"], fg=C["text2"])

        btn.bind("<Button-1>", on_click)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        self.nav_buttons[key] = btn
        self.nav_bars[key] = bar

    def _show_page(self, key):
        C = self.C
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(bg=C["bg3"], fg=C["accent"])
                self.nav_bars[k].configure(bg=C["accent"])
            else:
                btn.configure(bg=C["bg2"], fg=C["text2"])
                self.nav_bars[k].configure(bg=C["bg2"])

        self._current_page = key
        for widget in self.page_container.winfo_children():
            widget.destroy()

        if key == "overview":
            self._build_overview_page()
        elif key == "log":
            self._build_log_page()
        elif key == "settings":
            self._build_settings_page()
        elif key in VARIABLES:
            self._build_var_page(key)

    # ---- 總覽頁 ----

    def _build_overview_page(self):
        C = self.C
        frame = tk.Frame(self.page_container, bg=C["bg"])
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text=self._t("overview_title"),
                 bg=C["bg"], fg=C["text"], font=FONT_H1, anchor="w"
                 ).pack(fill="x", pady=(0, 12))

        # SB 狀態
        sb = self._sb_status
        if sb is True:
            sb_text, sb_color = self._t("enabled"), C["success"]
        elif sb is False:
            sb_text, sb_color = self._t("disabled"), C["danger"]
        else:
            sb_text, sb_color = self._t("unknown"), C["warning"]

        sb_card = tk.Frame(frame, bg=C["card"],
                           highlightbackground=C["border"], highlightthickness=1)
        sb_card.pack(fill="x", pady=(0, 16))
        tk.Label(sb_card, text=f"  {self._t('sb_status')}",
                 bg=C["card"], fg=C["text2"], font=FONT_SANS, anchor="w"
                 ).pack(side="left", padx=16, pady=12)
        tk.Label(sb_card, text=sb_text,
                 bg=C["card"], fg=sb_color, font=FONT_H2, anchor="e"
                 ).pack(side="right", padx=16, pady=12)

        # 指標卡片
        cards_frame = tk.Frame(frame, bg=C["bg"])
        cards_frame.pack(fill="x", pady=(0, 16))

        for vname in VAR_ORDER:
            info = self.results.get(vname, {})
            entries = info.get("entries", [])
            error = info.get("error")
            x509_count = sum(1 for e in entries if "X.509" in e["type_name"])
            hash_count = len(entries) - x509_count

            if error:
                value, color = "ERR", C["danger"]
            elif entries:
                value, color = f"{len(entries)}", C["accent"]
            else:
                value, color = "0", C["muted"]

            card = tk.Frame(cards_frame, bg=C["card"],
                            highlightbackground=C["border"], highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=4)
            tk.Label(card, text=VARIABLES[vname]["label"],
                     bg=C["card"], fg=C["text2"], font=FONT_SANS_SM
                     ).pack(anchor="w", padx=12, pady=(10, 2))
            tk.Label(card, text=value,
                     bg=C["card"], fg=color, font=FONT_METRIC
                     ).pack(anchor="w", padx=12)
            detail = []
            if x509_count:
                detail.append(f"{x509_count} cert")
            if hash_count:
                detail.append(f"{hash_count} hash")
            tk.Label(card, text=", ".join(detail) if detail else "\u2014",
                     bg=C["card"], fg=C["muted"], font=FONT_SANS_SM
                     ).pack(anchor="w", padx=12, pady=(0, 10))

        # 憑證摘要
        tk.Label(frame, text=self._t("cert_summary"),
                 bg=C["bg"], fg=C["text"], font=FONT_H2, anchor="w"
                 ).pack(fill="x", pady=(8, 4))

        summary_frame = tk.Frame(frame, bg=C["card"],
                                 highlightbackground=C["border"], highlightthickness=1)
        summary_frame.pack(fill="both", expand=True)

        hdr = tk.Frame(summary_frame, bg=C["bg3"])
        hdr.pack(fill="x")
        for text, w in [(self._t("col_var"), 60), (self._t("col_type"), 140),
                         (self._t("col_subject"), 400)]:
            tk.Label(hdr, text=text, bg=C["bg3"], fg=C["text2"],
                     font=FONT_SANS_SM, anchor="w", width=w // 8
                     ).pack(side="left", padx=8, pady=6)

        for vname in VAR_ORDER:
            entries = self.results.get(vname, {}).get("entries", [])
            for e in entries:
                row = tk.Frame(summary_frame, bg=C["card"])
                row.pack(fill="x")
                tk.Label(row, text=vname, bg=C["card"], fg=C["accent"],
                         font=FONT_MONO_SM, anchor="w", width=8
                         ).pack(side="left", padx=8, pady=4)
                tk.Label(row, text=e["type_name"], bg=C["card"], fg=C["text2"],
                         font=FONT_SANS_SM, anchor="w", width=18
                         ).pack(side="left", padx=8, pady=4)
                if "X.509" in e["type_name"]:
                    cert = parse_certificate(e["data"])
                    display = cert.get("Subject", "-")[:60]
                elif e["type_name"] in HASH_TYPES:
                    display = e["data"].hex().upper()[:48] + "..."
                else:
                    display = "(other)"
                tk.Label(row, text=display, bg=C["card"], fg=C["text"],
                         font=FONT_MONO_SM, anchor="w"
                         ).pack(side="left", padx=8, pady=4, fill="x", expand=True)

    # ---- 變數頁 ----

    def _build_var_page(self, vname):
        C = self.C
        meta = VARIABLES[vname]
        info = self.results.get(vname, {})
        entries = info.get("entries", [])
        error = info.get("error")

        frame = tk.Frame(self.page_container, bg=C["bg"])
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text=meta["label"],
                 bg=C["bg"], fg=C["text"], font=FONT_H1, anchor="w"
                 ).pack(fill="x")
        tk.Label(frame, text=meta["desc"],
                 bg=C["bg"], fg=C["text2"], font=FONT_SANS_SM, anchor="w"
                 ).pack(fill="x", pady=(0, 12))

        if error:
            tk.Label(frame, text=self._t("error_read").format(error),
                     bg=C["bg"], fg=C["danger"], font=FONT_SANS, anchor="w"
                     ).pack(fill="x", pady=24)
            return
        if not entries:
            tk.Label(frame, text=self._t("no_data"),
                     bg=C["bg"], fg=C["muted"], font=FONT_SANS, anchor="w"
                     ).pack(fill="x", pady=24)
            return

        paned = tk.PanedWindow(frame, orient="horizontal", bg=C["bg"],
                               sashwidth=4, sashrelief="flat")
        paned.pack(fill="both", expand=True)

        left = tk.Frame(paned, bg=C["tree_bg"])
        paned.add(left, width=380)

        cols = ("idx", "type", "size")
        tree = ttk.Treeview(left, columns=cols, show="headings",
                            selectmode="browse", style="Treeview")
        tree.heading("idx", text=self._t("col_idx"))
        tree.heading("type", text=self._t("col_type"))
        tree.heading("size", text=self._t("col_size"))
        tree.column("idx", width=40, anchor="center")
        tree.column("type", width=180)
        tree.column("size", width=80, anchor="e")

        sb = ttk.Scrollbar(left, orient="vertical", command=tree.yview,
                           style="Vertical.TScrollbar")
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        for i, e in enumerate(entries, 1):
            tree.insert("", "end", values=(i, e["type_name"],
                                           f"{e['data_size']} B"))

        right = tk.Frame(paned, bg=C["bg"])
        paned.add(right, width=500)

        detail_text = tk.Text(right, bg=C["bg"], fg=C["text"],
                              font=FONT_MONO, relief="flat",
                              padx=12, pady=12, wrap="word",
                              insertbackground=C["text"],
                              selectbackground=C["accent"])
        detail_text.pack(fill="both", expand=True)
        detail_text.insert("1.0", self._t("select_item"))
        detail_text.configure(state="disabled")

        def on_select(event):
            sel = tree.selection()
            if not sel:
                return
            idx = int(tree.item(sel[0])["values"][0]) - 1
            if 0 <= idx < len(entries):
                self._show_entry_detail(detail_text, entries[idx])

        tree.bind("<<TreeviewSelect>>", on_select)

    def _show_entry_detail(self, text_widget, entry):
        C = self.C
        text_widget.configure(state="normal")
        text_widget.delete("1.0", "end")

        lines = [
            f"{self._t('sig_type')}:  {entry['type_name']}",
            f"{self._t('type_guid')}: {entry['type_guid']}",
            f"{self._t('owner')}:     {entry['owner_guid']}",
            f"{self._t('data_size')}:  {entry['data_size']} bytes",
            "",
        ]

        if "X.509" in entry["type_name"]:
            cert = parse_certificate(entry["data"])
            lines.append(self._t("cert_info"))
            lines.append("")
            for k, v in cert.items():
                # 長值自動換行並對齊 (v00.00.1c fix)
                prefix = f"  {k:16s} "
                wrapped = textwrap.fill(
                    str(v), width=72,
                    initial_indent=prefix,
                    subsequent_indent=" " * len(prefix),
                )
                lines.append(wrapped)
        elif entry["type_name"] in HASH_TYPES:
            lines.append(self._t("hash_value"))
            lines.append("")
            lines.append(f"  {entry['data'].hex().upper()}")
        else:
            lines.append(self._t("raw_data"))
            lines.append("")
            lines.append(parsers.hex_dump(entry["data"]))

        text_widget.insert("1.0", "\n".join(lines))
        text_widget.configure(state="disabled")

    # ---- 日誌頁 ----

    def _build_log_page(self):
        C = self.C
        frame = tk.Frame(self.page_container, bg=C["bg"])
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text=self._t("log_title"),
                 bg=C["bg"], fg=C["text"], font=FONT_H1, anchor="w"
                 ).pack(fill="x", pady=(0, 12))

        log_text = tk.Text(frame, bg=C["bg2"], fg=C["text2"],
                           font=FONT_MONO_SM, relief="flat",
                           padx=12, pady=12, wrap="word")
        log_text.pack(fill="both", expand=True)

        for vname in VAR_ORDER:
            info = self.results.get(vname, {})
            entries = info.get("entries", [])
            error = info.get("error")
            if error:
                log_text.insert("end", f"[ERROR] {vname}: {error}\n", "error")
            else:
                log_text.insert("end",
                    f"[OK] {vname}: {len(entries)} entries loaded\n")

        log_text.tag_configure("error", foreground=C["danger"])
        log_text.configure(state="disabled")

    # ---- 設定頁 (v00.00.1b 新增) ----

    def _build_settings_page(self):
        C = self.C
        frame = tk.Frame(self.page_container, bg=C["bg"])
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text=self._t("settings_title"),
                 bg=C["bg"], fg=C["text"], font=FONT_H1, anchor="w"
                 ).pack(fill="x", pady=(0, 16))

        # === UI 風格 ===
        theme_card = tk.Frame(frame, bg=C["card"],
                              highlightbackground=C["border"], highlightthickness=1)
        theme_card.pack(fill="x", pady=(0, 12))

        tk.Label(theme_card, text=self._t("ui_theme"),
                 bg=C["card"], fg=C["text"], font=FONT_H2, anchor="w"
                 ).pack(fill="x", padx=16, pady=(12, 4))
        tk.Label(theme_card, text=self._t("restart_hint"),
                 bg=C["card"], fg=C["muted"], font=FONT_SANS_SM, anchor="w"
                 ).pack(fill="x", padx=16)

        btn_frame = tk.Frame(theme_card, bg=C["card"])
        btn_frame.pack(fill="x", padx=16, pady=(8, 16))

        theme_options = [
            ("dark", self._t("theme_dark")),
            ("light", self._t("theme_light")),
            ("system", self._t("theme_system")),
        ]
        for mode, label in theme_options:
            is_active = (self.theme_mode == mode)
            b = tk.Button(btn_frame, text=label,
                          bg=C["accent"] if is_active else C["bg3"],
                          fg="#ffffff" if is_active else C["text"],
                          activebackground=C["accent"],
                          font=FONT_SANS, relief="flat", padx=20, pady=8,
                          command=lambda m=mode: self._set_theme(m))
            b.pack(side="left", padx=4)

        # === 語言 ===
        lang_card = tk.Frame(frame, bg=C["card"],
                             highlightbackground=C["border"], highlightthickness=1)
        lang_card.pack(fill="x", pady=(0, 12))

        tk.Label(lang_card, text=self._t("language"),
                 bg=C["card"], fg=C["text"], font=FONT_H2, anchor="w"
                 ).pack(fill="x", padx=16, pady=(12, 4))
        tk.Label(lang_card, text=self._t("restart_hint"),
                 bg=C["card"], fg=C["muted"], font=FONT_SANS_SM, anchor="w"
                 ).pack(fill="x", padx=16)

        lang_btn_frame = tk.Frame(lang_card, bg=C["card"])
        lang_btn_frame.pack(fill="x", padx=16, pady=(8, 16))

        for lang_code, lang_name in LANGS.items():
            is_active = (self.lang == lang_code)
            b = tk.Button(lang_btn_frame, text=lang_name,
                          bg=C["accent"] if is_active else C["bg3"],
                          fg="#ffffff" if is_active else C["text"],
                          activebackground=C["accent"],
                          font=FONT_SANS, relief="flat", padx=20, pady=8,
                          command=lambda lc=lang_code: self._set_lang(lc))
            b.pack(side="left", padx=4)

        # === 版權 ===
        copyright_card = tk.Frame(frame, bg=C["card"],
                                  highlightbackground=C["border"], highlightthickness=1)
        copyright_card.pack(fill="x", pady=(0, 12))

        tk.Label(copyright_card, text=self._t("copyright"),
                 bg=C["card"], fg=C["text"], font=FONT_H2, anchor="w"
                 ).pack(fill="x", padx=16, pady=(12, 4))

        copyright_text = self._t("copyright_text")
        tk.Label(copyright_card, text=copyright_text,
                 bg=C["card"], fg=C["muted"], font=FONT_SANS_SM, anchor="w",
                 justify="left").pack(fill="x", padx=16, pady=(0, 16))

    def _set_theme(self, mode):
        """切換 UI 主題並重建介面。"""
        self.theme_mode = mode
        self._rebuild_ui()

    def _set_lang(self, lang_code):
        """切換 UI 語言並重建介面。"""
        self.lang = lang_code
        self._rebuild_ui()

    # ---- 資料載入 ----

    def _start_load(self):
        if self.busy:
            return
        self.busy = True
        self.status_var.set(self._t("loading"))
        self.sb_label.configure(text=self._t("sb_checking"))

        def worker():
            sb = get_secure_boot_status()
            self.queue.put(("sb_status", sb))
            for vname in VAR_ORDER:
                self.queue.put(("progress",
                    self._t("loading_var").format(vname)))
                try:
                    raw = collectors.read_uefi_variable(vname)
                    entries = parsers.parse_signature_list(raw)
                    self.results[vname] = {"entries": entries, "error": None}
                except Exception as e:
                    self.results[vname] = {"entries": [], "error": str(e)}
                self.queue.put(("var_done", vname))
            self.queue.put(("done", None))

        threading.Thread(target=worker, daemon=True).start()
        self._poll_queue()

    def _poll_queue(self):
        try:
            while True:
                msg_type, payload = self.queue.get_nowait()
                if msg_type == "sb_status":
                    self._sb_status = payload
                    C = self.C
                    if payload is True:
                        self.sb_label.configure(
                            text=self._t("sb_enabled"), fg=C["success"])
                    elif payload is False:
                        self.sb_label.configure(
                            text=self._t("sb_disabled"), fg=C["danger"])
                    else:
                        self.sb_label.configure(
                            text=self._t("sb_unknown"), fg=C["warning"])
                elif msg_type == "progress":
                    self.status_var.set(payload)
                elif msg_type == "var_done":
                    if self._current_page == payload:
                        self._show_page(payload)
                elif msg_type == "done":
                    self.busy = False
                    self.status_var.set(self._t("load_complete"))
                    if self._current_page:
                        self._show_page(self._current_page)
                    return
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    # ---- 匯出 ----

    def _export_report(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[
                (self._t("html_report"), "*.html"),
                (self._t("txt_report"), "*.txt"),
                ("Markdown", "*.md"),
                (self._t("all_files"), "*.*"),
            ],
            title=self._t("export_title"),
        )
        if not path:
            return
        try:
            if path.endswith(".txt"):
                report.export_text(path, self.results, self.lang)
            elif path.endswith(".md"):
                report.export_markdown(path, self.results, self.lang)
            else:
                report.export_html(path, self.results, self.lang)
            messagebox.showinfo(
                self._t("export_success"),
                f"{self._t('export_saved')}\n{path}")
        except Exception as e:
            messagebox.showerror(self._t("export_fail"), str(e))
