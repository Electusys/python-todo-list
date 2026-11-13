#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Yapılacaklar listesi — tkinter arayüz + SQLite kalıcılık + Açık/Koyu Tema (tek dosya)."""

from __future__ import annotations

import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Optional


DB_PATH = Path(__file__).resolve().parent / "todos.db"

# Görsel tema paletleri
THEMES: dict[str, dict[str, str]] = {
    "light": {
        "bg": "#f4f6f8",
        "card": "#ffffff",
        "border": "#d8dee6",
        "text": "#1f2933",
        "muted": "#6b7785",
        "accent": "#2f6fed",
        "accent_hover": "#2458c7",
        "done": "#8c9ba5",
        "danger": "#c62828",
        "selected": "#e8eefc",
        "del_hover": "#fdecea",
        "entry_bg": "#ffffff",
        "entry_fg": "#1f2933",
        "scrollbar_bg": "#d8dee6",
        "scrollbar_trough": "#f4f6f8",
    },
    "dark": {
        "bg": "#18191a",
        "card": "#242526",
        "border": "#3a3b3c",
        "text": "#e4e6eb",
        "muted": "#9a9fa8",
        "accent": "#3a82f7",
        "accent_hover": "#2f6fed",
        "done": "#6c727d",
        "danger": "#ef5350",
        "selected": "#2e384d",
        "del_hover": "#3e2426",
        "entry_bg": "#3a3b3c",
        "entry_fg": "#e4e6eb",
        "scrollbar_bg": "#3a3b3c",
        "scrollbar_trough": "#18191a",
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

    def close(self) -> None:
        self.conn.close()


class TodoApp(tk.Tk):
    def __init__(self, store: Optional[TodoStore] = None) -> None:
        super().__init__()
        self.store = store or TodoStore()
        self.theme_name = self.store.get_setting("theme", "light")
        if self.theme_name not in THEMES:
            self.theme_name = "light"
        self.colors = THEMES[self.theme_name]

        self.title("Yapılacaklar Listesi")
        self.minsize(520, 420)
        self.geometry("640x520")

        self._build_ui()
        self._apply_theme()
        self.refresh()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_theme(self) -> None:
        colors = THEMES[self.theme_name]
        self.colors = colors

        self.configure(bg=colors["bg"])
        if hasattr(self, "canvas"):
            self.canvas.configure(bg=colors["card"])
        if hasattr(self, "theme_btn"):
            if self.theme_name == "dark":
                self.theme_btn.configure(text="☀️ Açık Mod")
            else:
                self.theme_btn.configure(text="🌙 Koyu Mod")

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Root.TFrame", background=colors["bg"])
        style.configure("Card.TFrame", background=colors["card"])
        style.configure(
            "Title.TLabel",
            background=colors["bg"],
            foreground=colors["text"],
            font=("Segoe UI Semibold", 18),
        )
        style.configure(
            "Subtitle.TLabel",
            background=colors["bg"],
            foreground=colors["muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Hint.TLabel",
            background=colors["card"],
            foreground=colors["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "Status.TLabel",
            background=colors["bg"],
            foreground=colors["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "Accent.TButton",
            font=("Segoe UI Semibold", 10),
            padding=(14, 8),
            background=colors["accent"],
            foreground="#ffffff",
        )
        style.map(
            "Accent.TButton",
            foreground=[("!disabled", "#ffffff")],
            background=[
                ("pressed", colors["accent_hover"]),
                ("active", colors["accent_hover"]),
                ("!disabled", colors["accent"]),
            ],
        )
        style.configure(
            "Tool.TButton",
            font=("Segoe UI", 9),
            padding=(10, 6),
            background=colors["card"],
            foreground=colors["text"],
        )
        style.map(
            "Tool.TButton",
            background=[
                ("pressed", colors["selected"]),
                ("active", colors["selected"]),
                ("!disabled", colors["card"]),
            ],
            foreground=[("!disabled", colors["text"])],
        )
        style.configure(
            "Danger.TButton",
            font=("Segoe UI", 9),
            padding=(10, 6),
            background=colors["card"],
        )
        style.map(
            "Danger.TButton",
            foreground=[("!disabled", colors["danger"])],
            background=[
                ("pressed", colors["del_hover"]),
                ("active", colors["del_hover"]),
                ("!disabled", colors["card"]),
            ],
        )
        style.configure(
            "Theme.TButton",
            font=("Segoe UI", 9),
            padding=(8, 6),
            background=colors["card"],
            foreground=colors["text"],
        )
        style.map(
            "Theme.TButton",
            background=[
                ("pressed", colors["selected"]),
                ("active", colors["selected"]),
                ("!disabled", colors["card"]),
            ],
            foreground=[("!disabled", colors["text"])],
        )
        style.configure(
            "TEntry",
            fieldbackground=colors["entry_bg"],
            foreground=colors["entry_fg"],
            insertcolor=colors["text"],
            bordercolor=colors["border"],
            lightcolor=colors["border"],
            darkcolor=colors["border"],
        )
        style.configure(
            "TCheckbutton",
            background=colors["card"],
            foreground=colors["text"],
            focuscolor=colors["card"],
        )
        style.map(
            "TCheckbutton",
            background=[("active", colors["card"]), ("!disabled", colors["card"])],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=colors["scrollbar_bg"],
            troughcolor=colors["scrollbar_trough"],
            bordercolor=colors["card"],
            arrowcolor=colors["text"],
        )

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Başlık ve Tema Butonu
        header = ttk.Frame(self, style="Root.TFrame", padding=(20, 18, 20, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        title_frame = ttk.Frame(header, style="Root.TFrame")
        title_frame.grid(row=0, column=0, sticky="w")

        ttk.Label(title_frame, text="Yapılacaklar", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            title_frame,
            text="Görevleriniz bu bilgisayarda SQLite ile saklanır.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        self.theme_btn = ttk.Button(
            header,
            style="Theme.TButton",
            command=self.toggle_theme,
            cursor="hand2",
        )
        self.theme_btn.grid(row=0, column=1, sticky="e")

        # Gövde
        body = ttk.Frame(self, style="Root.TFrame", padding=(20, 8, 20, 8))
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        # Ekleme kartı
        add_card = ttk.Frame(body, style="Card.TFrame", padding=14)
        add_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        add_card.columnconfigure(0, weight=1)

        self.entry = ttk.Entry(add_card, font=("Segoe UI", 11))
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry.bind("<Return>", lambda _e: self.add_task())

        add_btn = ttk.Button(
            add_card,
            text="Ekle",
            style="Accent.TButton",
            command=self.add_task,
        )
        add_btn.grid(row=0, column=1, sticky="e")

        ttk.Label(
            add_card,
            text="Enter ile de ekleyebilirsiniz.",
            style="Hint.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))

        # Liste kartı
        list_card = ttk.Frame(body, style="Card.TFrame", padding=(10, 10, 6, 10))
        list_card.grid(row=1, column=0, sticky="nsew")
        list_card.columnconfigure(0, weight=1)
        list_card.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            list_card,
            highlightthickness=0,
            bd=0,
        )
        self.scrollbar = ttk.Scrollbar(
            list_card, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.list_frame = ttk.Frame(self.canvas, style="Card.TFrame")
        self._list_window = self.canvas.create_window(
            (0, 0), window=self.list_frame, anchor="nw"
        )

        self.list_frame.bind("<Configure>", self._on_list_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Alt araç çubuğu
        footer = ttk.Frame(self, style="Root.TFrame", padding=(20, 4, 20, 16))
        footer.grid(row=2, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)

        self.status = ttk.Label(footer, text="", style="Status.TLabel")
        self.status.grid(row=0, column=0, sticky="w")

        tools = ttk.Frame(footer, style="Root.TFrame")
        tools.grid(row=0, column=1, sticky="e")

        ttk.Button(
            tools,
            text="Tamamla / Geri Al",
            style="Tool.TButton",
            command=self.toggle_selected,
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            tools,
            text="Sil",
            style="Danger.TButton",
            command=self.delete_selected,
        ).pack(side="left")

        self._selected_id: Optional[int] = None
        self._row_widgets: dict[int, tk.Frame] = {}

    def toggle_theme(self) -> None:
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self.store.set_setting("theme", self.theme_name)
        self._apply_theme()
        self.refresh()

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

    def refresh(self) -> None:
        self._clear_list()
        tasks = self.store.list_tasks()

        if not tasks:
            empty = tk.Label(
                self.list_frame,
                text="Henüz görev yok. Yukarıdan ekleyin.",
                bg=self.colors["card"],
                fg=self.colors["muted"],
                font=("Segoe UI", 11),
                pady=28,
            )
            empty.pack(fill="x")
            self.status.configure(text="0 görev")
            return

        done_count = sum(1 for t in tasks if t["done"])
        self.status.configure(
            text=f"{len(tasks)} görev · {done_count} tamamlandı"
        )

        for task in tasks:
            self._add_row(task["id"], task["text"], bool(task["done"]))

    def _add_row(self, task_id: int, text: str, done: bool) -> None:
        card_bg = self.colors["card"]
        row = tk.Frame(self.list_frame, bg=card_bg, padx=8, pady=6)
        row.pack(fill="x", pady=2)
        self._row_widgets[task_id] = row

        check_var = tk.BooleanVar(value=done)

        def on_toggle() -> None:
            self.store.set_done(task_id, check_var.get())
            self.refresh()

        check = ttk.Checkbutton(
            row,
            variable=check_var,
            command=on_toggle,
            style="TCheckbutton",
        )
        check.pack(side="left", padx=(0, 8))

        label_fg = self.colors["done"] if done else self.colors["text"]
        label_font = ("Segoe UI", 11, "overstrike") if done else ("Segoe UI", 11)
        label = tk.Label(
            row,
            text=text,
            bg=card_bg,
            fg=label_fg,
            font=label_font,
            anchor="w",
            justify="left",
            wraplength=480,
            cursor="hand2",
        )
        label.pack(side="left", fill="x", expand=True)

        def select(_event=None, tid=task_id) -> None:
            self._select(tid)

        for widget in (row, label):
            widget.bind("<Button-1>", select)
            widget.bind("<Double-Button-1>", lambda _e, tid=task_id: self._toggle_by_id(tid))

        del_btn = tk.Button(
            row,
            text="✕",
            font=("Segoe UI", 9),
            fg=self.colors["danger"],
            bg=card_bg,
            activebackground=self.colors["del_hover"],
            activeforeground=self.colors["danger"],
            relief="flat",
            bd=0,
            cursor="hand2",
            command=lambda tid=task_id: self._delete_by_id(tid),
        )
        del_btn.pack(side="right", padx=(8, 0))

    def _select(self, task_id: int) -> None:
        self._selected_id = task_id
        sel_bg = self.colors["selected"]
        card_bg = self.colors["card"]
        for tid, frame in self._row_widgets.items():
            current_bg = sel_bg if tid == task_id else card_bg
            frame.configure(bg=current_bg)
            for child in frame.winfo_children():
                if isinstance(child, (tk.Label, tk.Button)):
                    child.configure(bg=current_bg)

    def _toggle_by_id(self, task_id: int) -> None:
        tasks = {t["id"]: t for t in self.store.list_tasks()}
        task = tasks.get(task_id)
        if not task:
            return
        self.store.set_done(task_id, not bool(task["done"]))
        self.refresh()

    def _delete_by_id(self, task_id: int) -> None:
        if not messagebox.askyesno("Sil", "Bu görev silinsin mi?"):
            return
        self.store.delete(task_id)
        self.refresh()

    def add_task(self) -> None:
        text = self.entry.get().strip()
        if not text:
            messagebox.showinfo("Bilgi", "Lütfen bir görev yazın.")
            return
        self.store.add(text)
        self.entry.delete(0, tk.END)
        self.refresh()
        self.entry.focus_set()

    def toggle_selected(self) -> None:
        if self._selected_id is None:
            messagebox.showinfo("Bilgi", "Önce bir görev seçin.")
            return
        self._toggle_by_id(self._selected_id)

    def delete_selected(self) -> None:
        if self._selected_id is None:
            messagebox.showinfo("Bilgi", "Önce bir görev seçin.")
            return
        self._delete_by_id(self._selected_id)

    def _on_close(self) -> None:
        try:
            self.canvas.unbind_all("<MouseWheel>")
        except tk.TclError:
            pass
        self.store.close()
        self.destroy()


def main() -> None:
    app = TodoApp()
    app.mainloop()


if __name__ == "__main__":
    main()
