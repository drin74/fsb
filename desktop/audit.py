"""Audit log window for the desktop client."""
from __future__ import annotations

import tkinter.messagebox as messagebox
from tkinter import ttk

import customtkinter as ctk

from api import ApiClient, ApiError, AuthExpired
from theme import (
    BG,
    DIM,
    GOLD,
    LINE,
    MUTED,
    PANEL,
    PANEL_2,
    RED,
    TEXT,
    button,
    card,
    configure_treeview_style,
    entry,
    font,
    label,
)

ACTION_LABELS = {
    "create": "Создание",
    "update": "Изменение",
    "delete": "Удаление",
    "view": "Просмотр",
    "login": "Вход",
    "logout": "Выход",
    "import": "Импорт",
    "export": "Экспорт",
}
ACTION_REVERSE = {v: k for k, v in ACTION_LABELS.items()}
PAGE_SIZE = 40


def fmt_dt(value):
    if not value:
        return "—"
    try:
        import datetime as dt

        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d.%m.%Y %H:%M:%S")
    except ValueError:
        return value


class AuditWindow(ctk.CTkToplevel):
    def __init__(self, master, api: ApiClient):
        super().__init__(master)
        configure_treeview_style()
        self.api = api
        self.page = 1
        self.pages = 1

        self.title("Журнал аудита")
        self.geometry("1220x760")
        self.minsize(980, 620)
        self.configure(fg_color=BG)
        self.transient(master)

        header = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0)
        header.pack(fill="x")
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", padx=22, pady=14)
        label(left, "КОНТРОЛЬ ДОСТУПА", 8, GOLD, "bold").pack(anchor="w")
        label(left, "Журнал аудита", 20, TEXT, "bold").pack(anchor="w")
        button(header, "Закрыть", self.destroy, "ghost", 90).pack(side="right", padx=18)

        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.pack(fill="x", padx=20, pady=(14, 8))
        self.search = entry(filters, "Объект, сотрудник, модель…", 320)
        self.search.pack(side="left", padx=(0, 8))
        self.search.bind("<Return>", lambda _e: self.load(1))
        self.action_combo = ctk.CTkComboBox(
            filters, values=["Все действия"] + list(ACTION_LABELS.values()), state="readonly",
            width=150, height=34, fg_color=PANEL, border_color=LINE, button_color=PANEL_2,
            dropdown_fg_color=PANEL_2, font=font(10.5),
            command=lambda _v: self.load(1),
        )
        self.action_combo.pack(side="left", padx=(0, 8))
        self.action_combo.set("Все действия")
        button(filters, "Найти", lambda: self.load(1), "ghost", 80).pack(side="left")
        self.counter = label(filters, "", 9, DIM)
        self.counter.pack(side="right")

        box = card(self)
        box.pack(fill="both", expand=True, padx=20, pady=(0, 8))
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(0, weight=1)

        columns = ("time", "user", "action", "object", "model", "ip")
        self.tree = ttk.Treeview(box, columns=columns, show="headings", style="FSB.Treeview")
        widths = {"time": 150, "user": 160, "action": 100, "object": 380, "model": 140, "ip": 110}
        titles = {
            "time": "Время", "user": "Сотрудник", "action": "Действие",
            "object": "Объект", "model": "Модель", "ip": "IP",
        }
        for column in columns:
            self.tree.heading(column, text=titles[column], anchor="w")
            self.tree.column(column, width=widths[column], stretch=column == "object", anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        scroll = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview, style="FSB.Vertical.TScrollbar")
        scroll.grid(row=0, column=1, sticky="ns", pady=8, padx=(0, 6))
        self.tree.configure(yscrollcommand=scroll.set)

        pager = ctk.CTkFrame(self, fg_color="transparent")
        pager.pack(fill="x", padx=20, pady=(0, 12))
        self.prev_btn = button(pager, "← Назад", lambda: self.load(self.page - 1), "ghost", 90, 30)
        self.prev_btn.pack(side="left")
        self.page_label = label(pager, "Страница 1", 9.5, MUTED)
        self.page_label.pack(side="left", padx=12)
        self.next_btn = button(pager, "Вперёд →", lambda: self.load(self.page + 1), "ghost", 90, 30)
        self.next_btn.pack(side="left")

        self.load(1)

    def load(self, page=1):
        page = max(1, page)
        action = ACTION_REVERSE.get(self.action_combo.get(), "")
        try:
            data = self.api.audit(page=page, search=self.search.get().strip(), action=action)
        except AuthExpired:
            messagebox.showerror("Сессия", "Сессия истекла.", parent=self)
            self.destroy()
            return
        except ApiError as exc:
            messagebox.showerror("Ошибка", str(exc), parent=self)
            return

        count = data.get("count", 0)
        self.page = page
        self.pages = max(1, -(-count // PAGE_SIZE))
        self.tree.delete(*self.tree.get_children())
        for log in data.get("results", []):
            self.tree.insert(
                "", "end",
                values=(
                    fmt_dt(log.get("created_at")),
                    log.get("user_name") or "система",
                    ACTION_LABELS.get(log.get("action"), log.get("action")),
                    (log.get("object_repr") or "—")[:80],
                    log.get("model_name") or "—",
                    log.get("ip") or "—",
                ),
            )
        self.page_label.configure(text=f"Страница {self.page} из {self.pages}")
        self.counter.configure(text=f"Записей: {count}")
        self.prev_btn.configure(state="normal" if self.page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.page < self.pages else "disabled")
