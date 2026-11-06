"""Tkinter 圖形介面 — GitHub Dark 設計系統 (VVT 風格)。

與 ModernStandbyTester 同一設計語言：
  深色背景 (#0d1117/#161b22/#21262d)、藍色重點 (#58a6ff)、
  左側 200px 導覽側邊欄（active：3px 藍色左邊框）、
  頂部動作工具列、底部狀態列、指標卡片、扁平按鈕、
  Segoe UI + Cascadia Code 字體。
"""

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import collectors, parsers, report
from .certs import parse_certificate
from .collectors import VARIABLES, VAR_ORDER, get_secure_boot_status, is_admin
from .parsers import HASH_TYPES
from .version import VERSION

APP_TITLE = "Secure Boot Key Viewer"

# ---- GitHub Dark 設計系統 tokens ----
C = {
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
}
FONT_SANS = ("Segoe UI", 10)
FONT_SANS_SM = ("Segoe UI", 9)
FONT_MONO = ("Cascadia Code", 10)
FONT_MONO_SM = ("Cascadia Code", 9)
FONT_H1 = ("Segoe UI", 14, "bold")
FONT_H2 = ("Segoe UI", 12, "bold")
FONT_METRIC = ("Cascadia Code", 18, "bold")
FONT_ICON = ("Segoe UI Emoji", 16)

STATUS_COLORS = {
    "PASS": C["success"],
    "WARN": C["warning"],
    "FAIL": C["danger"],
    "INFO": C["accent"],
}

NAV_ITEMS = [
    ("overview", "📋", "總覽"),
    ("PK", "🔑", "PK"),
    ("KEK", "🔐", "KEK"),
    ("db", "✅", "db"),
    ("dbx", "🚫", "dbx"),
    ("log", "📜", "日誌"),
]


class App(tk.Tk):
    """主視窗。"""

    def __init__(self, use_mock=False):
        super().__init__()
        self.use_mock = use_mock
        self.results = {}  # {var_name: {"entries": [...], "error": str|None}}
        self.queue = queue.Queue()
        self.busy = False
        self.pages = {}
        self.nav_buttons = {}
        self.nav_bars = {}
        self._current_page = None
        self._sb_status = None

        self.title(f"🔐 {APP_TITLE} {VERSION}")
        self.geometry("1100x740")
        self.minsize(900, 600)
        self.configure(bg=C["bg"])

        self._build_layout()
        self._show_page("overview")

        # 啟動資料載入
        self.after(200, self._start_load)

        # 權限提示
        if not is_admin():
            self.after(500, lambda: messagebox.showwarning(
                "需要管理員權限",
                "讀取 UEFI Secure Boot 變數需要系統管理員權限。\n"
                "請以「以系統管理員身分執行」重新啟動本程式。",
            ))

    # ---- UI 建構 ----

    def _build_layout(self):
        """建立整體版面: 側邊欄 + 主內容區 + 狀態列。"""
        # 側邊欄
        sidebar = tk.Frame(self, bg=C["bg2"], width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # 側邊欄標題
        tk.Label(
            sidebar, text="🔐 SBK Viewer", bg=C["bg2"],
            fg=C["accent"], font=FONT_H2, anchor="w", padx=16, pady=16,
        ).pack(fill="x")

        # 導覽按鈕
        for key, icon, label in NAV_ITEMS:
            self._make_nav_button(sidebar, key, icon, label)

        # 側邊欄底部: 版號
        tk.Label(
            sidebar, text=f"  {VERSION}", bg=C["bg2"],
            fg=C["muted"], font=FONT_SANS_SM, anchor="w",
        ).pack(side="bottom", fill="x", pady=8)

        # 主內容區
        main = tk.Frame(self, bg=C["bg"])
        main.pack(side="left", fill="both", expand=True)

        # 頂部工具列
        toolbar = tk.Frame(main, bg=C["bg2"], height=48)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        tk.Button(
            toolbar, text="🔄 重新讀取", bg=C["bg3"], fg=C["text"],
            activebackground=C["accent"], activeforeground=C["bg"],
            font=FONT_SANS, relief="flat", padx=16, pady=6,
            command=self._start_load,
        ).pack(side="left", padx=(12, 4), pady=8)

        tk.Button(
            toolbar, text="💾 匯出報告", bg=C["bg3"], fg=C["text"],
            activebackground=C["accent"], activeforeground=C["bg"],
            font=FONT_SANS, relief="flat", padx=16, pady=6,
            command=self._export_report,
        ).pack(side="left", padx=4, pady=8)

        # SB 狀態標籤
        self.sb_label = tk.Label(
            toolbar, text="Secure Boot: 檢查中...",
            bg=C["bg2"], fg=C["text2"], font=FONT_SANS,
        )
        self.sb_label.pack(side="right", padx=16)

        # 頁面容器
        self.page_container = tk.Frame(main, bg=C["bg"])
        self.page_container.pack(fill="both", expand=True, padx=16, pady=12)

        # 狀態列
        self.status_var = tk.StringVar(value="就緒")
        status_bar = tk.Label(
            self, textvariable=self.status_var,
            bg=C["bg2"], fg=C["text2"], font=FONT_SANS_SM,
            anchor="w", padx=12, pady=4,
        )
        status_bar.pack(side="bottom", fill="x")

    def _make_nav_button(self, parent, key, icon, label):
        """建立側邊欄導覽按鈕 (含 active 狀態藍色左邊框)。"""
        container = tk.Frame(parent, bg=C["bg2"])
        container.pack(fill="x")

        # 藍色左邊框 (active indicator)
        bar = tk.Frame(container, bg=C["bg2"], width=3)
        bar.pack(side="left", fill="y")

        btn = tk.Label(
            container, text=f"  {icon}  {label}",
            bg=C["bg2"], fg=C["text2"], font=FONT_SANS,
            anchor="w", padx=12, pady=10, cursor="hand2",
        )
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
        """切換顯示指定頁面。"""
        # 更新導覽狀態
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(bg=C["bg3"], fg=C["accent"])
                self.nav_bars[k].configure(bg=C["accent"])
            else:
                btn.configure(bg=C["bg2"], fg=C["text2"])
                self.nav_bars[k].configure(bg=C["bg2"])

        self._current_page = key

        # 清除舊頁面
        for widget in self.page_container.winfo_children():
            widget.destroy()

        # 建立新頁面
        if key == "overview":
            self._build_overview_page()
        elif key == "log":
            self._build_log_page()
        elif key in VARIABLES:
            self._build_var_page(key)

    # ---- 頁面: 總覽 ----

    def _build_overview_page(self):
        """總覽頁面: Secure Boot 狀態 + 各變數摘要卡片。"""
        frame = tk.Frame(self.page_container, bg=C["bg"])
        frame.pack(fill="both", expand=True)

        # 標題
        tk.Label(
            frame, text="📋 Secure Boot 金鑰總覽",
            bg=C["bg"], fg=C["text"], font=FONT_H1, anchor="w",
        ).pack(fill="x", pady=(0, 12))

        # SB 狀態卡片
        sb = self._sb_status
        if sb is True:
            sb_text, sb_color = "✅ 已啟用", C["success"]
        elif sb is False:
            sb_text, sb_color = "❌ 未啟用", C["danger"]
        else:
            sb_text, sb_color = "⚠️ 無法確定", C["warning"]

        sb_card = tk.Frame(frame, bg=C["card"], highlightbackground=C["border"],
                           highlightthickness=1)
        sb_card.pack(fill="x", pady=(0, 16))

        tk.Label(
            sb_card, text="  Secure Boot 狀態",
            bg=C["card"], fg=C["text2"], font=FONT_SANS, anchor="w",
        ).pack(side="left", padx=16, pady=12)

        tk.Label(
            sb_card, text=sb_text,
            bg=C["card"], fg=sb_color, font=FONT_H2, anchor="e",
        ).pack(side="right", padx=16, pady=12)

        # 各變數指標卡片
        cards_frame = tk.Frame(frame, bg=C["bg"])
        cards_frame.pack(fill="x", pady=(0, 16))

        for vname in VAR_ORDER:
            info = self.results.get(vname, {})
            entries = info.get("entries", [])
            error = info.get("error")

            x509_count = sum(1 for e in entries if "X.509" in e["type_name"])
            hash_count = len(entries) - x509_count

            if error:
                value, color = "錯誤", C["danger"]
            elif entries:
                value = f"{len(entries)}"
                color = C["accent"]
            else:
                value, color = "空", C["muted"]

            card = tk.Frame(cards_frame, bg=C["card"],
                            highlightbackground=C["border"],
                            highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=4)

            tk.Label(
                card, text=VARIABLES[vname]["label"],
                bg=C["card"], fg=C["text2"], font=FONT_SANS_SM,
            ).pack(anchor="w", padx=12, pady=(10, 2))

            tk.Label(
                card, text=value,
                bg=C["card"], fg=color, font=FONT_METRIC,
            ).pack(anchor="w", padx=12)

            detail = []
            if x509_count:
                detail.append(f"{x509_count} 憑證")
            if hash_count:
                detail.append(f"{hash_count} 雜湊")

            tk.Label(
                card, text=", ".join(detail) if detail else "—",
                bg=C["card"], fg=C["muted"], font=FONT_SANS_SM,
            ).pack(anchor="w", padx=12, pady=(0, 10))

        # 憑證摘要列表
        tk.Label(
            frame, text="憑證摘要",
            bg=C["bg"], fg=C["text"], font=FONT_H2, anchor="w",
        ).pack(fill="x", pady=(8, 4))

        summary_frame = tk.Frame(frame, bg=C["card"],
                                 highlightbackground=C["border"],
                                 highlightthickness=1)
        summary_frame.pack(fill="both", expand=True)

        # 標題列
        hdr = tk.Frame(summary_frame, bg=C["bg3"])
        hdr.pack(fill="x")
        for text, w in [("變數", 60), ("類型", 140), ("Subject / 雜湊", 400)]:
            tk.Label(
                hdr, text=text, bg=C["bg3"], fg=C["text2"],
                font=FONT_SANS_SM, anchor="w", width=w // 8,
            ).pack(side="left", padx=8, pady=6)

        # 憑證列
        for vname in VAR_ORDER:
            entries = self.results.get(vname, {}).get("entries", [])
            for e in entries:
                row = tk.Frame(summary_frame, bg=C["card"])
                row.pack(fill="x")

                tk.Label(
                    row, text=vname, bg=C["card"], fg=C["accent"],
                    font=FONT_MONO_SM, anchor="w", width=8,
                ).pack(side="left", padx=8, pady=4)

                tk.Label(
                    row, text=e["type_name"], bg=C["card"], fg=C["text2"],
                    font=FONT_SANS_SM, anchor="w", width=18,
                ).pack(side="left", padx=8, pady=4)

                if "X.509" in e["type_name"]:
                    cert = parse_certificate(e["data"])
                    display = cert.get("Subject", "-")[:60]
                elif e["type_name"] in HASH_TYPES:
                    display = e["data"].hex().upper()[:48] + "..."
                else:
                    display = "(其他)"

                tk.Label(
                    row, text=display, bg=C["card"], fg=C["text"],
                    font=FONT_MONO_SM, anchor="w",
                ).pack(side="left", padx=8, pady=4, fill="x", expand=True)

    # ---- 頁面: 個別變數 ----

    def _build_var_page(self, vname):
        """個別變數頁面: 左側簽章列表 + 右側詳細資訊。"""
        meta = VARIABLES[vname]
        info = self.results.get(vname, {})
        entries = info.get("entries", [])
        error = info.get("error")

        frame = tk.Frame(self.page_container, bg=C["bg"])
        frame.pack(fill="both", expand=True)

        # 標題
        tk.Label(
            frame, text=f"{meta['label']}",
            bg=C["bg"], fg=C["text"], font=FONT_H1, anchor="w",
        ).pack(fill="x")
        tk.Label(
            frame, text=meta["desc"],
            bg=C["bg"], fg=C["text2"], font=FONT_SANS_SM, anchor="w",
        ).pack(fill="x", pady=(0, 12))

        if error:
            tk.Label(
                frame, text=f"❌ 讀取錯誤: {error}",
                bg=C["bg"], fg=C["danger"], font=FONT_SANS, anchor="w",
            ).pack(fill="x", pady=24)
            return

        if not entries:
            tk.Label(
                frame, text="(此變數無資料)",
                bg=C["bg"], fg=C["muted"], font=FONT_SANS, anchor="w",
            ).pack(fill="x", pady=24)
            return

        # PanedWindow: 左列表 + 右詳情
        paned = tk.PanedWindow(frame, orient="horizontal", bg=C["bg"],
                               sashwidth=4, sashrelief="flat")
        paned.pack(fill="both", expand=True)

        # 左側: 簽章列表 (Treeview)
        left = tk.Frame(paned, bg=C["bg2"])
        paned.add(left, width=380)

        cols = ("idx", "type", "size")
        tree = ttk.Treeview(left, columns=cols, show="headings",
                            selectmode="browse")
        tree.heading("idx", text="#")
        tree.heading("type", text="類型")
        tree.heading("size", text="大小")
        tree.column("idx", width=40, anchor="center")
        tree.column("type", width=180)
        tree.column("size", width=80, anchor="e")

        sb = ttk.Scrollbar(left, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        for i, e in enumerate(entries, 1):
            tree.insert("", "end", values=(
                i, e["type_name"], f"{e['data_size']} B"
            ))

        # 右側: 詳細資訊
        right = tk.Frame(paned, bg=C["bg"])
        paned.add(right, width=500)

        detail_text = tk.Text(
            right, bg=C["bg"], fg=C["text"], font=FONT_MONO,
            relief="flat", padx=12, pady=12, wrap="word",
            insertbackground=C["text"],
        )
        detail_text.pack(fill="both", expand=True)
        detail_text.insert("1.0", "← 請選擇左側項目以查看詳細資訊")
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
        """在文字區域顯示單筆簽章的詳細資訊。"""
        text_widget.configure(state="normal")
        text_widget.delete("1.0", "end")

        lines = [
            f"簽章類型:  {entry['type_name']}",
            f"類型 GUID: {entry['type_guid']}",
            f"Owner:     {entry['owner_guid']}",
            f"資料大小:  {entry['data_size']} bytes",
            "",
        ]

        if "X.509" in entry["type_name"]:
            cert = parse_certificate(entry["data"])
            lines.append("═══ X.509 憑證資訊 ═══")
            lines.append("")
            for k, v in cert.items():
                lines.append(f"  {k:16s} {v}")
        elif entry["type_name"] in HASH_TYPES:
            lines.append("═══ 雜湊值 ═══")
            lines.append("")
            lines.append(f"  {entry['data'].hex().upper()}")
        else:
            lines.append("═══ 原始資料 (hex dump) ═══")
            lines.append("")
            lines.append(parsers.hex_dump(entry["data"]))

        text_widget.insert("1.0", "\n".join(lines))
        text_widget.configure(state="disabled")

    # ---- 頁面: 日誌 ----

    def _build_log_page(self):
        """日誌頁面: 顯示載入過程記錄。"""
        frame = tk.Frame(self.page_container, bg=C["bg"])
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame, text="📜 操作日誌",
            bg=C["bg"], fg=C["text"], font=FONT_H1, anchor="w",
        ).pack(fill="x", pady=(0, 12))

        log_text = tk.Text(
            frame, bg=C["bg2"], fg=C["text2"], font=FONT_MONO_SM,
            relief="flat", padx=12, pady=12, wrap="word",
        )
        log_text.pack(fill="both", expand=True)

        # 顯示結果摘要
        for vname in VAR_ORDER:
            info = self.results.get(vname, {})
            entries = info.get("entries", [])
            error = info.get("error")

            if error:
                log_text.insert("end", f"[ERROR] {vname}: {error}\n", "error")
            else:
                log_text.insert("end",
                    f"[OK] {vname}: {len(entries)} 筆簽章已載入\n")

        log_text.tag_configure("error", foreground=C["danger"])
        log_text.configure(state="disabled")

    # ---- 資料載入 ----

    def _start_load(self):
        """在背景執行緒載入所有 UEFI 變數。"""
        if self.busy:
            return
        self.busy = True
        self.status_var.set("載入中...")
        self.sb_label.configure(text="Secure Boot: 檢查中...")

        def worker():
            # Secure Boot 狀態
            sb = get_secure_boot_status()
            self.queue.put(("sb_status", sb))

            # 讀取各變數
            for vname in VAR_ORDER:
                self.queue.put(("progress", f"讀取 {vname}..."))
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
        """輪詢背景執行緒的訊息佇列並更新 UI。"""
        try:
            while True:
                msg_type, payload = self.queue.get_nowait()

                if msg_type == "sb_status":
                    self._sb_status = payload
                    if payload is True:
                        self.sb_label.configure(
                            text="Secure Boot: ✅ 已啟用", fg=C["success"])
                    elif payload is False:
                        self.sb_label.configure(
                            text="Secure Boot: ❌ 未啟用", fg=C["danger"])
                    else:
                        self.sb_label.configure(
                            text="Secure Boot: ⚠️ 無法確定", fg=C["warning"])

                elif msg_type == "progress":
                    self.status_var.set(payload)

                elif msg_type == "var_done":
                    # 如果正在檢視該變數頁面，重新整理
                    if self._current_page == payload:
                        self._show_page(payload)

                elif msg_type == "done":
                    self.busy = False
                    self.status_var.set("載入完成")
                    # 刷新當前頁面
                    if self._current_page:
                        self._show_page(self._current_page)
                    return  # 停止輪詢

        except queue.Empty:
            pass

        self.after(100, self._poll_queue)

    # ---- 報告匯出 ----

    def _export_report(self):
        """匯出報告 (Markdown 或 HTML)。"""
        path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[
                ("HTML 報告", "*.html"),
                ("Markdown 報告", "*.md"),
                ("所有檔案", "*.*"),
            ],
            title="匯出 Secure Boot 報告",
        )
        if not path:
            return

        try:
            if path.endswith(".md"):
                report.export_markdown(path, self.results)
            else:
                report.export_html(path, self.results)
            messagebox.showinfo("匯出成功", f"報告已儲存至:\n{path}")
        except Exception as e:
            messagebox.showerror("匯出失敗", str(e))


# ---- Mock 示範資料 (供 UI 開發測試) ----

def make_mock_results():
    """產生示範用的 mock 資料。"""
    return {
        "PK": {"entries": [], "error": None},
        "KEK": {"entries": [], "error": None},
        "db": {"entries": [], "error": None},
        "dbx": {"entries": [], "error": None},
    }
