#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Yapılacaklar — cilalı masaüstü arayüz + SQLite (tek dosya, stdlib)."""

from __future__ import annotations

import sqlite3
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Optional


DB_PATH = Path(__file__).resolve().parent / "todos.db"


def send_notification(title: str, message: str) -> None:
    """Windows yerel bildirimi (telefondaki push için mobil APK gerekir)."""
    try:
        from winotify import Notification, audio

        toast = Notification(
            app_id="Yapılacaklar",
            title=title,
            msg=message,
            duration="short",
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
        return
    except Exception:
        pass
    try:
        from plyer import notification

        notification.notify(
            title=title, message=message, app_name="Yapılacaklar", timeout=10
        )
    except Exception:
        pass

# Görsel kimlik: teal / mürekkep (mor-beyaz AI klişesi yok)
THEMES: dict[str, dict[str, str]] = {
    "light": {
        "bg": "#eef3f1",
        "bg_accent": "#e2ebe8",
        "card": "#ffffff",
        "card_border": "#cfdcd7",
        "row": "#ffffff",
        "row_hover": "#f3faf7",
        "row_selected": "#d8f3ea",
        "text": "#12352f",
        "muted": "#5f746e",
        "accent": "#0f8a75",
        "accent_hover": "#0b6f5e",
        "accent_soft": "#d5f0e8",
        "done": "#8a9b96",
        "danger": "#c62828",
        "danger_soft": "#fdecea",
        "entry_bg": "#f7fbf9",
        "entry_fg": "#12352f",
        "entry_border": "#b7ccc4",
        "chip_bg": "#dff3ec",
        "chip_fg": "#0b6f5e",
        "shadow": "#d5e2dd",
    },
    "dark": {
        "bg": "#101917",
        "bg_accent": "#15221f",
        "card": "#1a2824",
        "card_border": "#2c3f39",
        "row": "#1a2824",
        "row_hover": "#21332e",
        "row_selected": "#24443b",
        "text": "#e7f2ee",
        "muted": "#93a8a1",
        "accent": "#2dd4bf",
        "accent_hover": "#5eead4",
        "accent_soft": "#1d3a34",
        "done": "#7f918b",
        "danger": "#f07167",
        "danger_soft": "#3a2423",
        "entry_bg": "#24352f",
        "entry_fg": "#e7f2ee",
        "entry_border": "#3a5149",
        "chip_bg": "#1d3a34",
        "chip_fg": "#5eead4",
        "shadow": "#0b1210",
    },
}


class TodoStore:
    """SQLite üzerinden görev ve ayar kalıcılığı."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                remind_at TEXT NOT NULL,
                notified INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
        self.conn.commit()

    def get_setting(self, key: str, default: str = "") -> str:
        cur = self.conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        row = cur.fetchone()
        return str(row["value"]) if row else default

    def set_setting(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        self.conn.commit()

    def list_tasks(self) -> list[sqlite3.Row]:
        cur = self.conn.execute(
            "SELECT id, text, done FROM todos ORDER BY done ASC, id DESC"
        )
        return list(cur.fetchall())

    def add(self, text: str) -> None:
        self.conn.execute("INSERT INTO todos (text) VALUES (?)", (text,))
        self.conn.commit()

    def set_done(self, task_id: int, done: bool) -> None:
        self.conn.execute(
            "UPDATE todos SET done = ? WHERE id = ?",
            (1 if done else 0, task_id),
        )
        self.conn.commit()

    def delete(self, task_id: int) -> None:
        self.conn.execute("DELETE FROM todos WHERE id = ?", (task_id,))
        self.conn.commit()

    def list_reminders(self) -> list[sqlite3.Row]:
        cur = self.conn.execute(
            """
            SELECT id, title, remind_at, notified
            FROM reminders
            ORDER BY notified ASC, remind_at ASC
            """
        )
        return list(cur.fetchall())

    def add_reminder(self, title: str, remind_at: str) -> None:
        self.conn.execute(
            "INSERT INTO reminders (title, remind_at) VALUES (?, ?)",
            (title, remind_at),
        )
        self.conn.commit()

    def delete_reminder(self, rem_id: int) -> None:
        self.conn.execute("DELETE FROM reminders WHERE id = ?", (rem_id,))
        self.conn.commit()

    def due_reminders(self, now: str) -> list[sqlite3.Row]:
        cur = self.conn.execute(
            """
            SELECT id, title, remind_at FROM reminders
            WHERE notified = 0 AND remind_at <= ?
            ORDER BY remind_at ASC
            """,
            (now,),
        )
        return list(cur.fetchall())

    def mark_reminder_notified(self, rem_id: int) -> None:
        self.conn.execute(
            "UPDATE reminders SET notified = 1 WHERE id = ?", (rem_id,)
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


class CircleCheck(tk.Canvas):
    """Özel dairesel tamamlanma kontrolü."""

    def __init__(
        self,
        master: tk.Misc,
        checked: bool,
        colors: dict[str, str],
        command=None,
        size: int = 22,
    ) -> None:
        super().__init__(
            master,
            width=size,
            height=size,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.size = size
        self.checked = checked
        self.colors = colors
        self.command = command
        self.configure(bg=colors["row"])
        self.bind("<Button-1>", self._toggle)
        self.bind("<Enter>", self._hover_on)
        self.bind("<Leave>", self._hover_off)
        self._hover = False
        self.redraw()

    def set_colors(self, colors: dict[str, str], bg: str) -> None:
        self.colors = colors
        self.configure(bg=bg)
        self.redraw()

    def set_checked(self, checked: bool) -> None:
        self.checked = checked
        self.redraw()

    def _toggle(self, _event=None) -> None:
        self.checked = not self.checked
        self.redraw()
        if self.command:
            self.command(self.checked)

    def _hover_on(self, _event=None) -> None:
        self._hover = True
        self.redraw()

    def _hover_off(self, _event=None) -> None:
        self._hover = False
        self.redraw()

    def redraw(self) -> None:
        self.delete("all")
        pad = 2
        x0, y0, x1, y1 = pad, pad, self.size - pad, self.size - pad
        outline = self.colors["accent"] if (self.checked or self._hover) else self.colors["entry_border"]
        fill = self.colors["accent"] if self.checked else self.colors["row"]
        self.create_oval(x0, y0, x1, y1, outline=outline, width=2, fill=fill)
        if self.checked:
            self.create_line(
                pad + 4,
                self.size // 2,
                self.size // 2 - 1,
                self.size - pad - 5,
                self.size - pad - 4,
                pad + 5,
                fill="#ffffff",
                width=2,
                capstyle=tk.ROUND,
                joinstyle=tk.ROUND,
            )


class TodoApp(tk.Tk):
    def __init__(self, store: Optional[TodoStore] = None) -> None:
        super().__init__()
        self.store = store or TodoStore()
        self.theme_name = self.store.get_setting("theme", "light")
        if self.theme_name not in THEMES:
            self.theme_name = "light"
        self.colors = THEMES[self.theme_name]

        self.title("Yapılacaklar")
        self.minsize(560, 480)
        self.geometry("700x580")

        self._selected_id: Optional[int] = None
        self._row_widgets: dict[int, dict] = {}
        self._flash_after: Optional[str] = None
        self._view = "tasks"  # tasks | reminders
        self._poll_after: Optional[str] = None

        self._build_ui()
        self._apply_theme()
        self.refresh()
        self.refresh_reminders()
        self.show_view("tasks")
        self.after(80, lambda: self.entry.focus_set())
        self._poll_reminders()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ theme
    def _apply_theme(self) -> None:
        c = THEMES[self.theme_name]
        self.colors = c
        self.configure(bg=c["bg"])

        if hasattr(self, "theme_btn"):
            self.theme_btn.configure(
                text="Açık tema" if self.theme_name == "dark" else "Koyu tema"
            )

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Root.TFrame", background=c["bg"])
        style.configure("Card.TFrame", background=c["card"])
        style.configure(
            "Brand.TLabel",
            background=c["bg"],
            foreground=c["accent"],
            font=("Segoe UI Semibold", 11),
        )
        style.configure(
            "Title.TLabel",
            background=c["bg"],
            foreground=c["text"],
            font=("Segoe UI Semibold", 22),
        )
        style.configure(
            "Subtitle.TLabel",
            background=c["bg"],
            foreground=c["muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Section.TLabel",
            background=c["card"],
            foreground=c["muted"],
            font=("Segoe UI Semibold", 9),
        )
        style.configure(
            "Hint.TLabel",
            background=c["card"],
            foreground=c["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "Status.TLabel",
            background=c["bg"],
            foreground=c["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "Flash.TLabel",
            background=c["bg"],
            foreground=c["accent"],
            font=("Segoe UI Semibold", 9),
        )
        style.configure(
            "Chip.TLabel",
            background=c["chip_bg"],
            foreground=c["chip_fg"],
            font=("Segoe UI Semibold", 9),
            padding=(10, 4),
        )
        style.configure(
            "Accent.TButton",
            font=("Segoe UI Semibold", 10),
            padding=(16, 9),
            background=c["accent"],
            foreground="#ffffff",
            borderwidth=0,
            focusthickness=0,
        )
        style.map(
            "Accent.TButton",
            foreground=[("!disabled", "#ffffff")],
            background=[
                ("pressed", c["accent_hover"]),
                ("active", c["accent_hover"]),
                ("!disabled", c["accent"]),
            ],
        )
        style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 9),
            padding=(12, 7),
            background=c["card"],
            foreground=c["text"],
            bordercolor=c["card_border"],
            lightcolor=c["card_border"],
            darkcolor=c["card_border"],
            relief="solid",
            borderwidth=1,
        )
        style.map(
            "Secondary.TButton",
            background=[
                ("pressed", c["row_selected"]),
                ("active", c["row_hover"]),
                ("!disabled", c["card"]),
            ],
            foreground=[("!disabled", c["text"])],
        )
        style.configure(
            "Danger.TButton",
            font=("Segoe UI", 9),
            padding=(12, 7),
            background=c["card"],
            foreground=c["danger"],
            bordercolor=c["card_border"],
            lightcolor=c["card_border"],
            darkcolor=c["card_border"],
            relief="solid",
            borderwidth=1,
        )
        style.map(
            "Danger.TButton",
            foreground=[("!disabled", c["danger"])],
            background=[
                ("pressed", c["danger_soft"]),
                ("active", c["danger_soft"]),
                ("!disabled", c["card"]),
            ],
        )
        style.configure(
            "Ghost.TButton",
            font=("Segoe UI", 9),
            padding=(10, 6),
            background=c["bg"],
            foreground=c["muted"],
            borderwidth=0,
        )
        style.map(
            "Ghost.TButton",
            background=[
                ("pressed", c["bg_accent"]),
                ("active", c["bg_accent"]),
                ("!disabled", c["bg"]),
            ],
            foreground=[("!disabled", c["muted"]), ("active", c["text"])],
        )
        style.configure(
            "Todo.TEntry",
            fieldbackground=c["entry_bg"],
            foreground=c["entry_fg"],
            insertcolor=c["text"],
            bordercolor=c["entry_border"],
            lightcolor=c["entry_border"],
            darkcolor=c["entry_border"],
            padding=8,
        )
        style.map(
            "Todo.TEntry",
            bordercolor=[("focus", c["accent"])],
            lightcolor=[("focus", c["accent"])],
            darkcolor=[("focus", c["accent"])],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=c["card_border"],
            troughcolor=c["card"],
            bordercolor=c["card"],
            arrowcolor=c["muted"],
        )

        if hasattr(self, "canvas"):
            self.canvas.configure(bg=c["card"])
        if hasattr(self, "accent_bar"):
            self.accent_bar.configure(bg=c["accent"])
        if hasattr(self, "add_shell"):
            self.add_shell.configure(bg=c["card"], highlightbackground=c["card_border"])
        if hasattr(self, "list_shell"):
            self.list_shell.configure(bg=c["card"], highlightbackground=c["card_border"])
        if hasattr(self, "rem_shell"):
            self.rem_shell.configure(bg=c["card"], highlightbackground=c["card_border"])
        if hasattr(self, "rem_add_shell"):
            self.rem_add_shell.configure(
                bg=c["card"], highlightbackground=c["card_border"]
            )
        if hasattr(self, "chip"):
            self.chip.configure(background=c["chip_bg"], foreground=c["chip_fg"])
        if hasattr(self, "nav_tasks"):
            self._style_nav()

    # -------------------------------------------------------------------- UI
    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # Üst marka / başlık
        header = ttk.Frame(self, style="Root.TFrame", padding=(28, 22, 28, 6))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        left = ttk.Frame(header, style="Root.TFrame")
        left.grid(row=0, column=0, sticky="w")

        brand_row = ttk.Frame(left, style="Root.TFrame")
        brand_row.pack(anchor="w")
        ttk.Label(brand_row, text="FOCUS", style="Brand.TLabel").pack(side="left")
        self.chip = ttk.Label(brand_row, text="0 kalan", style="Chip.TLabel")
        self.chip.pack(side="left", padx=(10, 0))

        ttk.Label(left, text="Yapılacaklar", style="Title.TLabel").pack(
            anchor="w", pady=(6, 0)
        )
        ttk.Label(
            left,
            text="Görevler ve hatırlatıcılar bu bilgisayarda saklanır.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        nav = ttk.Frame(left, style="Root.TFrame")
        nav.pack(anchor="w", pady=(12, 0))
        self.nav_tasks = ttk.Button(
            nav,
            text="Görevler",
            style="Secondary.TButton",
            command=lambda: self.show_view("tasks"),
            cursor="hand2",
        )
        self.nav_tasks.pack(side="left", padx=(0, 8))
        self.nav_reminders = ttk.Button(
            nav,
            text="Hatırlatıcılar",
            style="Secondary.TButton",
            command=lambda: self.show_view("reminders"),
            cursor="hand2",
        )
        self.nav_reminders.pack(side="left")

        self.theme_btn = ttk.Button(
            header,
            style="Ghost.TButton",
            command=self.toggle_theme,
            cursor="hand2",
        )
        self.theme_btn.grid(row=0, column=1, sticky="ne")

        self.accent_bar = tk.Frame(self, height=3, bd=0, highlightthickness=0)
        self.accent_bar.grid(row=1, column=0, sticky="ew", padx=28, pady=(10, 4))

        # Gövde — iki görünüm
        body = ttk.Frame(self, style="Root.TFrame", padding=(28, 10, 28, 8))
        body.grid(row=2, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)
        self.body = body

        self.tasks_view = ttk.Frame(body, style="Root.TFrame")
        self.tasks_view.columnconfigure(0, weight=1)
        self.tasks_view.rowconfigure(1, weight=1)

        self.reminders_view = ttk.Frame(body, style="Root.TFrame")
        self.reminders_view.columnconfigure(0, weight=1)
        self.reminders_view.rowconfigure(1, weight=1)

        # Ekleme alanı
        self.add_shell = tk.Frame(
            self.tasks_view,
            bd=0,
            highlightthickness=1,
            padx=16,
            pady=14,
        )
        self.add_shell.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        self.add_shell.columnconfigure(0, weight=1)

        add_inner = ttk.Frame(self.add_shell, style="Card.TFrame")
        add_inner.grid(row=0, column=0, sticky="ew")
        add_inner.columnconfigure(0, weight=1)

        ttk.Label(add_inner, text="YENİ GÖREV", style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )

        self.entry = ttk.Entry(add_inner, font=("Segoe UI", 12), style="Todo.TEntry")
        self.entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        self.entry.bind("<Return>", lambda _e: self.add_task())

        ttk.Button(
            add_inner,
            text="Ekle",
            style="Accent.TButton",
            command=self.add_task,
            cursor="hand2",
        ).grid(row=1, column=1, sticky="e")

        ttk.Label(
            add_inner,
            text="Enter ile hızlı ekleyin · çift tık ile tamamlayın",
            style="Hint.TLabel",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))

        # Liste alanı
        self.list_shell = tk.Frame(
            self.tasks_view,
            bd=0,
            highlightthickness=1,
            padx=8,
            pady=8,
        )
        self.list_shell.grid(row=1, column=0, sticky="nsew")
        self.list_shell.columnconfigure(0, weight=1)
        self.list_shell.rowconfigure(1, weight=1)

        list_header = ttk.Frame(self.list_shell, style="Card.TFrame")
        list_header.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 6))
        list_header.columnconfigure(0, weight=1)
        ttk.Label(list_header, text="GÖREVLER", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        self.canvas = tk.Canvas(self.list_shell, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(
            self.list_shell, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        self.scrollbar.grid(row=1, column=1, sticky="ns")

        self.list_frame = ttk.Frame(self.canvas, style="Card.TFrame")
        self._list_window = self.canvas.create_window(
            (0, 0), window=self.list_frame, anchor="nw"
        )
        self.list_frame.bind("<Configure>", self._on_list_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # ---- Hatırlatıcılar görünümü ----
        self.rem_add_shell = tk.Frame(
            self.reminders_view,
            bd=0,
            highlightthickness=1,
            padx=16,
            pady=14,
        )
        self.rem_add_shell.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        self.rem_add_shell.columnconfigure(0, weight=1)

        rem_inner = ttk.Frame(self.rem_add_shell, style="Card.TFrame")
        rem_inner.grid(row=0, column=0, sticky="ew")
        rem_inner.columnconfigure(0, weight=1)

        ttk.Label(rem_inner, text="YENİ HATIRLATICI", style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )
        self.rem_title = ttk.Entry(
            rem_inner, font=("Segoe UI", 12), style="Todo.TEntry"
        )
        self.rem_title.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        self.rem_title.insert(0, "")
        ttk.Button(
            rem_inner,
            text="Kur",
            style="Accent.TButton",
            command=self.add_reminder,
            cursor="hand2",
        ).grid(row=1, column=1, sticky="e")

        when = ttk.Frame(rem_inner, style="Card.TFrame")
        when.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Label(when, text="Tarih/saat:", style="Hint.TLabel").pack(
            side="left", padx=(0, 8)
        )
        soon = datetime.now() + timedelta(hours=1)
        self.rem_date = ttk.Entry(when, width=12, font=("Segoe UI", 10), style="Todo.TEntry")
        self.rem_date.insert(0, soon.strftime("%Y-%m-%d"))
        self.rem_date.pack(side="left", padx=(0, 8))
        self.rem_time = ttk.Entry(when, width=8, font=("Segoe UI", 10), style="Todo.TEntry")
        self.rem_time.insert(0, soon.strftime("%H:%M"))
        self.rem_time.pack(side="left")
        ttk.Label(
            rem_inner,
            text="Örn: Yarın 15:00 toplantı — zamanı gelince Windows bildirimi gelir.",
            style="Hint.TLabel",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))

        self.rem_shell = tk.Frame(
            self.reminders_view,
            bd=0,
            highlightthickness=1,
            padx=8,
            pady=8,
        )
        self.rem_shell.grid(row=1, column=0, sticky="nsew")
        self.rem_shell.columnconfigure(0, weight=1)
        self.rem_shell.rowconfigure(1, weight=1)

        rem_header = ttk.Frame(self.rem_shell, style="Card.TFrame")
        rem_header.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 6))
        ttk.Label(rem_header, text="HATIRLATICILAR", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        self.rem_canvas = tk.Canvas(self.rem_shell, highlightthickness=0, bd=0)
        self.rem_scroll = ttk.Scrollbar(
            self.rem_shell, orient="vertical", command=self.rem_canvas.yview
        )
        self.rem_canvas.configure(yscrollcommand=self.rem_scroll.set)
        self.rem_canvas.grid(row=1, column=0, sticky="nsew")
        self.rem_scroll.grid(row=1, column=1, sticky="ns")
        self.rem_list = ttk.Frame(self.rem_canvas, style="Card.TFrame")
        self._rem_window = self.rem_canvas.create_window(
            (0, 0), window=self.rem_list, anchor="nw"
        )
        self.rem_list.bind(
            "<Configure>",
            lambda _e: self.rem_canvas.configure(
                scrollregion=self.rem_canvas.bbox("all")
            ),
        )
        self.rem_canvas.bind(
            "<Configure>",
            lambda e: self.rem_canvas.itemconfigure(self._rem_window, width=e.width),
        )

        # Alt çubuk
        footer = ttk.Frame(self, style="Root.TFrame", padding=(28, 6, 28, 18))
        footer.grid(row=3, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)

        status_col = ttk.Frame(footer, style="Root.TFrame")
        status_col.grid(row=0, column=0, sticky="w")
        self.status = ttk.Label(status_col, text="", style="Status.TLabel")
        self.status.pack(anchor="w")
        self.flash = ttk.Label(status_col, text="", style="Flash.TLabel")
        self.flash.pack(anchor="w", pady=(2, 0))

        self.task_tools = ttk.Frame(footer, style="Root.TFrame")
        self.task_tools.grid(row=0, column=1, sticky="e")
        ttk.Button(
            self.task_tools,
            text="Tamamla / Geri Al",
            style="Secondary.TButton",
            command=self.toggle_selected,
            cursor="hand2",
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            self.task_tools,
            text="Sil",
            style="Danger.TButton",
            command=self.delete_selected,
            cursor="hand2",
        ).pack(side="left")

    # -------------------------------------------------------------- helpers
    def _style_nav(self) -> None:
        if not hasattr(self, "nav_tasks"):
            return
        if self._view == "tasks":
            self.nav_tasks.configure(style="Accent.TButton")
            self.nav_reminders.configure(style="Secondary.TButton")
        else:
            self.nav_tasks.configure(style="Secondary.TButton")
            self.nav_reminders.configure(style="Accent.TButton")

    def show_view(self, view: str) -> None:
        self._view = view
        self.tasks_view.grid_forget()
        self.reminders_view.grid_forget()
        if view == "tasks":
            self.tasks_view.grid(row=0, column=0, sticky="nsew")
            self.task_tools.grid(row=0, column=1, sticky="e")
            self.entry.focus_set()
        else:
            self.reminders_view.grid(row=0, column=0, sticky="nsew")
            self.task_tools.grid_remove()
            self.rem_title.focus_set()
            self.refresh_reminders()
        self._style_nav()

    def toggle_theme(self) -> None:
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self.store.set_setting("theme", self.theme_name)
        self._apply_theme()
        self.refresh()
        self.refresh_reminders()

    def _flash_message(self, text: str) -> None:
        self.flash.configure(text=text)
        if self._flash_after is not None:
            try:
                self.after_cancel(self._flash_after)
            except tk.TclError:
                pass
        self._flash_after = self.after(
            2600, lambda: self.flash.configure(text="")
        )

    def _on_list_configure(self, _event=None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self.canvas.itemconfigure(self._list_window, width=event.width)

    def _on_mousewheel(self, event) -> None:
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _clear_list(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()
        self._row_widgets.clear()
        self._selected_id = None

    def _update_counts(self, total: int, done: int) -> None:
        remaining = total - done
        self.chip.configure(text=f"{remaining} kalan")
        if total == 0:
            self.status.configure(text="Liste boş · yeni bir görev ekleyin")
        else:
            self.status.configure(
                text=f"{total} görev · {remaining} kalan · {done} tamamlandı"
            )

    # ---------------------------------------------------------------- data UI
    def refresh(self) -> None:
        keep_selected = self._selected_id
        self._clear_list()
        tasks = self.store.list_tasks()
        done_count = sum(1 for t in tasks if t["done"])
        self._update_counts(len(tasks), done_count)

        if not tasks:
            self._show_empty_state()
            return

        for task in tasks:
            self._add_row(task["id"], task["text"], bool(task["done"]))

        if keep_selected is not None and keep_selected in self._row_widgets:
            self._select(keep_selected)

    def _show_empty_state(self) -> None:
        c = self.colors
        wrap = tk.Frame(self.list_frame, bg=c["card"], pady=36)
        wrap.pack(fill="both", expand=True)

        icon = tk.Canvas(
            wrap, width=64, height=64, bg=c["card"], highlightthickness=0, bd=0
        )
        icon.pack()
        icon.create_oval(8, 8, 56, 56, outline=c["accent"], width=2, fill=c["accent_soft"])
        icon.create_line(22, 33, 30, 41, 44, 25, fill=c["accent"], width=3, capstyle=tk.ROUND)

        tk.Label(
            wrap,
            text="Henüz görev yok",
            bg=c["card"],
            fg=c["text"],
            font=("Segoe UI Semibold", 13),
        ).pack(pady=(14, 4))
        tk.Label(
            wrap,
            text="Yukarıdaki alana yazıp Ekle’ye basın.\nİlk göreviniz burada görünecek.",
            bg=c["card"],
            fg=c["muted"],
            font=("Segoe UI", 10),
            justify="center",
        ).pack()

    def _add_row(self, task_id: int, text: str, done: bool) -> None:
        c = self.colors
        outer = tk.Frame(self.list_frame, bg=c["card"], padx=6, pady=3)
        outer.pack(fill="x")

        row = tk.Frame(outer, bg=c["row"], padx=12, pady=10, cursor="hand2")
        row.pack(fill="x")
        # ince ayırıcı çizgi hissi
        row.configure(highlightthickness=1, highlightbackground=c["card_border"])

        def on_toggle(checked: bool, tid=task_id) -> None:
            self.store.set_done(tid, checked)
            self.refresh()
            self._flash_message(
                "Görev tamamlandı" if checked else "Görev yeniden açıldı"
            )

        check = CircleCheck(row, checked=done, colors=c, command=on_toggle)
        check.pack(side="left", padx=(0, 12))

        label_fg = c["done"] if done else c["text"]
        label_font = ("Segoe UI", 11, "overstrike") if done else ("Segoe UI", 11)
        label = tk.Label(
            row,
            text=text,
            bg=c["row"],
            fg=label_fg,
            font=label_font,
            anchor="w",
            justify="left",
            wraplength=460,
            cursor="hand2",
        )
        label.pack(side="left", fill="x", expand=True)

        del_btn = tk.Label(
            row,
            text="Sil",
            bg=c["row"],
            fg=c["muted"],
            font=("Segoe UI Semibold", 9),
            padx=8,
            pady=2,
            cursor="hand2",
        )
        del_btn.pack(side="right", padx=(8, 0))

        self._row_widgets[task_id] = {
            "outer": outer,
            "row": row,
            "check": check,
            "label": label,
            "del": del_btn,
            "done": done,
        }

        def select(_e=None, tid=task_id) -> None:
            self._select(tid)

        def hover_on(_e=None, tid=task_id) -> None:
            if self._selected_id == tid:
                return
            self._paint_row(tid, self.colors["row_hover"])

        def hover_off(_e=None, tid=task_id) -> None:
            if self._selected_id == tid:
                return
            self._paint_row(tid, self.colors["row"])

        for w in (row, label):
            w.bind("<Button-1>", select)
            w.bind("<Double-Button-1>", lambda _e, tid=task_id: self._toggle_by_id(tid))
            w.bind("<Enter>", hover_on)
            w.bind("<Leave>", hover_off)

        def del_hover_on(_e=None) -> None:
            del_btn.configure(fg=c["danger"], bg=c["danger_soft"])

        def del_hover_off(_e=None) -> None:
            bg = (
                c["row_selected"]
                if self._selected_id == task_id
                else (c["row_hover"] if row.cget("bg") == c["row_hover"] else c["row"])
            )
            # safer: use selected/base
            if self._selected_id == task_id:
                bg = c["row_selected"]
            else:
                bg = c["row"]
            del_btn.configure(fg=c["muted"], bg=bg)

        del_btn.bind("<Enter>", del_hover_on)
        del_btn.bind("<Leave>", del_hover_off)
        del_btn.bind("<Button-1>", lambda _e, tid=task_id: self._delete_by_id(tid))

    def _paint_row(self, task_id: int, bg: str) -> None:
        widgets = self._row_widgets.get(task_id)
        if not widgets:
            return
        widgets["row"].configure(bg=bg, highlightbackground=self.colors["card_border"])
        widgets["label"].configure(bg=bg)
        widgets["del"].configure(bg=bg)
        widgets["check"].set_colors(self.colors, bg)

    def _select(self, task_id: int) -> None:
        self._selected_id = task_id
        c = self.colors
        for tid in self._row_widgets:
            self._paint_row(
                tid, c["row_selected"] if tid == task_id else c["row"]
            )

    def _toggle_by_id(self, task_id: int) -> None:
        tasks = {t["id"]: t for t in self.store.list_tasks()}
        task = tasks.get(task_id)
        if not task:
            return
        new_done = not bool(task["done"])
        self.store.set_done(task_id, new_done)
        self.refresh()
        self._flash_message(
            "Görev tamamlandı" if new_done else "Görev yeniden açıldı"
        )

    def _delete_by_id(self, task_id: int) -> None:
        tasks = {t["id"]: t for t in self.store.list_tasks()}
        task = tasks.get(task_id)
        preview = task["text"] if task else "bu görev"
        if len(preview) > 42:
            preview = preview[:42] + "…"
        if not messagebox.askyesno(
            "Görevi sil",
            f"“{preview}” kalıcı olarak silinsin mi?",
            icon="warning",
        ):
            return
        self.store.delete(task_id)
        self.refresh()
        self._flash_message("Görev silindi")

    def add_task(self) -> None:
        text = self.entry.get().strip()
        if not text:
            self._flash_message("Boş görev eklenemez")
            self.entry.focus_set()
            return
        self.store.add(text)
        self.entry.delete(0, tk.END)
        self.refresh()
        self.entry.focus_set()
        self._flash_message("Görev eklendi")

    def toggle_selected(self) -> None:
        if self._selected_id is None:
            self._flash_message("Önce bir görev seçin")
            return
        self._toggle_by_id(self._selected_id)

    def delete_selected(self) -> None:
        if self._selected_id is None:
            self._flash_message("Önce bir görev seçin")
            return
        self._delete_by_id(self._selected_id)

    def add_reminder(self) -> None:
        title = self.rem_title.get().strip()
        date_s = self.rem_date.get().strip()
        time_s = self.rem_time.get().strip()
        if not title:
            self._flash_message("Hatırlatıcı başlığı gerekli")
            return
        remind_at = f"{date_s} {time_s}"
        try:
            dt = datetime.strptime(remind_at, "%Y-%m-%d %H:%M")
        except ValueError:
            self._flash_message("Tarih/saat formatı: YYYY-MM-DD ve HH:MM")
            return
        if dt <= datetime.now():
            self._flash_message("Gelecek bir zaman seçin")
            return
        self.store.add_reminder(title, remind_at)
        self.rem_title.delete(0, tk.END)
        self.refresh_reminders()
        self._flash_message(f"Hatırlatıcı kuruldu · {remind_at}")

    def refresh_reminders(self) -> None:
        if not hasattr(self, "rem_list"):
            return
        for child in self.rem_list.winfo_children():
            child.destroy()
        c = self.colors
        items = self.store.list_reminders()
        if self._view == "reminders":
            waiting = sum(1 for r in items if not r["notified"])
            self.status.configure(
                text=f"{len(items)} hatırlatıcı · {waiting} bekliyor"
            )
        if not items:
            tk.Label(
                self.rem_list,
                text="Henüz hatırlatıcı yok.\nÖrn: Yarın 15:00 toplantı.",
                bg=c["card"],
                fg=c["muted"],
                font=("Segoe UI", 11),
                justify="center",
                pady=28,
            ).pack(fill="x")
            return
        for rem in items:
            self._add_reminder_row(
                rem["id"], rem["title"], rem["remind_at"], bool(rem["notified"])
            )

    def _add_reminder_row(
        self, rem_id: int, title: str, remind_at: str, notified: bool
    ) -> None:
        c = self.colors
        outer = tk.Frame(self.rem_list, bg=c["card"], padx=6, pady=3)
        outer.pack(fill="x")
        row = tk.Frame(outer, bg=c["row"], padx=12, pady=10)
        row.pack(fill="x")
        row.configure(highlightthickness=1, highlightbackground=c["card_border"])
        status = "Bildirildi" if notified else "Bekliyor"
        fg = c["done"] if notified else c["text"]
        info = tk.Label(
            row,
            text=f"{title}\n{remind_at}  ·  {status}",
            bg=c["row"],
            fg=fg,
            font=("Segoe UI", 11),
            justify="left",
            anchor="w",
        )
        info.pack(side="left", fill="x", expand=True)
        del_btn = tk.Label(
            row,
            text="Sil",
            bg=c["row"],
            fg=c["muted"],
            font=("Segoe UI Semibold", 9),
            padx=8,
            cursor="hand2",
        )
        del_btn.pack(side="right")

        def on_del(_e=None, rid=rem_id, preview=title) -> None:
            short = preview if len(preview) <= 42 else preview[:42] + "…"
            if not messagebox.askyesno(
                "Hatırlatıcıyı sil",
                f"“{short}” silinsin mi?",
                icon="warning",
            ):
                return
            self.store.delete_reminder(rid)
            self.refresh_reminders()
            self._flash_message("Hatırlatıcı silindi")

        del_btn.bind("<Button-1>", on_del)
        del_btn.bind(
            "<Enter>",
            lambda _e: del_btn.configure(fg=c["danger"], bg=c["danger_soft"]),
        )
        del_btn.bind(
            "<Leave>",
            lambda _e: del_btn.configure(fg=c["muted"], bg=c["row"]),
        )

    def _poll_reminders(self) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        due = self.store.due_reminders(now)
        for rem in due:
            send_notification("Hatırlatıcı", rem["title"])
            self.store.mark_reminder_notified(rem["id"])
            self._flash_message(f"Bildirim: {rem['title']}")
        if due:
            self.refresh_reminders()
        self._poll_after = self.after(15000, self._poll_reminders)

    def _on_close(self) -> None:
        try:
            self.canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass
        if self._flash_after is not None:
            try:
                self.after_cancel(self._flash_after)
            except tk.TclError:
                pass
        if self._poll_after is not None:
            try:
                self.after_cancel(self._poll_after)
            except tk.TclError:
                pass
        self.store.close()
        self.destroy()


def main() -> None:
    app = TodoApp()
    app.mainloop()


if __name__ == "__main__":
    main()
