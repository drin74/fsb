"""Main desktop window: registry table, stats and actions."""
from __future__ import annotations

import math
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from tkinter import ttk

import customtkinter as ctk

from api import ApiClient, ApiError, AuthExpired
from audit import AuditWindow
from client_form import ClientDialog
from detail import ClientDetailWindow
from theme import (
    AMBER,
    BG,
    CYAN,
    DIM,
    GOLD,
    GREEN,
    LINE,
    MUTED,
    PANEL,
    PANEL_2,
    PANEL_3,
    RED,
    RISK_COLORS,
    RISK_LABELS,
    STATUS_COLORS,
    STATUS_LABELS,
    TEXT,
    button,
    card,
    configure_treeview_style,
    entry,
    font,
    label,
)

PAGE_SIZE = 20
ALL_STATUS = "Все статусы"
ALL_RISK = "Любой риск"
STATUS_REVERSE = {v: k for k, v in STATUS_LABELS.items()}
RISK_REVERSE = {v: k for k, v in RISK_LABELS.items()}


def fmt_dt(value):
    if not value:
        return "—"
    try:
        import datetime as dt

        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return value


def fmt_date(value):
    if not value:
        return "—"
    try:
        import datetime as dt

        return dt.date.fromisoformat(value[:10]).strftime("%d.%m.%Y")
    except ValueError:
        return value


class ImportDialog(ctk.CTkToplevel):
    def __init__(self, master, api: ApiClient, on_done):
        super().__init__(master)
        self.api = api
        self.on_done = on_done
        self.path = ""
        self.sources = []
        self.source_map = {}

        self.title("Импорт записей")
        self.geometry("620x380")
        self.configure(fg_color=BG)
        self.transient(master)
        self.grab_set()

        label(self, "МАССОВАЯ ЗАГРУЗКА", 9, GOLD, "bold").pack(anchor="w", padx=24, pady=(20, 2))
        label(self, "Импорт CSV / XLSX", 20, TEXT, "bold").pack(anchor="w", padx=24)

        file_row = ctk.CTkFrame(self, fg_color="transparent")
        file_row.pack(fill="x", padx=24, pady=(18, 10))
        self.file_label = label(file_row, "Файл не выбран", 10.5, MUTED)
        self.file_label.pack(side="left", fill="x", expand=True)
        button(file_row, "Выбрать файл", self.pick_file, "ghost", 120).pack(side="right")

        source_row = ctk.CTkFrame(self, fg_color="transparent")
        source_row.pack(fill="x", padx=24, pady=4)
        label(source_row, "Источник", 9.5, MUTED).pack(anchor="w", pady=(0, 3))
        self.source_combo = ctk.CTkComboBox(
            source_row, values=["— не указан —"], state="readonly", height=34,
            fg_color="#0b131a", border_color=LINE, button_color=PANEL_2,
            dropdown_fg_color=PANEL, font=font(11),
        )
        self.source_combo.pack(fill="x")

        hint = label(self, "Обязательные колонки: Фамилия, Имя. Поддерживаются UTF-8 и CP1251.", 9.5, DIM)
        hint.pack(anchor="w", padx=24, pady=(12, 0))

        self.result = label(self, "", 10, MUTED, wraplength=560, justify="left")
        self.result.pack(anchor="w", padx=24, pady=(8, 0))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=24, side="bottom", pady=18)
        self.run_btn = button(actions, "Начать импорт", self.run, "primary", 150, 38)
        self.run_btn.pack(side="right")
        button(actions, "Отмена", self.destroy, "ghost", 90, 38).pack(side="right", padx=8)

        self.load_sources()

    def load_sources(self):
        try:
            data = self.api.sources()
            self.sources = data.get("results", [])
        except ApiError:
            self.sources = []
        self.source_map = {s["name"]: s["id"] for s in self.sources}
        self.source_combo.configure(values=["— не указан —"] + list(self.source_map))

    def pick_file(self):
        path = filedialog.askopenfilename(
            parent=self, title="Файл для импорта",
            filetypes=[("Таблицы", "*.csv *.xlsx *.xlsm"), ("Все файлы", "*.*")],
        )
        if path:
            self.path = path
            self.file_label.configure(text=path, text_color=TEXT)

    def run(self):
        if not self.path:
            messagebox.showwarning("Импорт", "Выберите файл.", parent=self)
            return
        source_id = self.source_map.get(self.source_combo.get())
        self.run_btn.configure(state="disabled", text="Импорт…")
        self.result.configure(text="Загрузка и обработка файла…", text_color=MUTED)
        self.update_idletasks()
        try:
            result = self.api.import_clients(self.path, source_id)
        except (ApiError, AuthExpired) as exc:
            self.result.configure(text=f"Ошибка: {exc}", text_color=RED)
            self.run_btn.configure(state="normal", text="Начать импорт")
            return
        errors = result.get("errors") or []
        text = f"Добавлено записей: {result.get('created', 0)} из {result.get('total_rows', 0)}."
        if errors:
            text += "\nПропущено: " + "; ".join(errors[:4])
        self.result.configure(text=text, text_color=GREEN if not errors else AMBER)
        self.run_btn.configure(state="normal", text="Повторить импорт")
        self.on_done()


class MainWindow(ctk.CTk):
    def __init__(self, api: ApiClient, config: dict, on_logout):
        super().__init__()
        configure_treeview_style()
        self.api = api
        self.config = config
        self.on_logout = on_logout
        self.page = 1
        self.pages = 1
        self.total = 0
        self.search_job = None
        self.rows: dict[str, dict] = {}

        self.title("ФСБ · Единый реестр")
        self.geometry("1420x880")
        self.minsize(1120, 720)
        self.configure(fg_color=BG)
        self._center()

        self._build()
        self.refresh()
        self.bind("<F5>", lambda _e: self.refresh())
        self.bind("<Control-n>", lambda _e: self.add_client())
        self.bind("<Delete>", lambda _e: self.delete_selected())

    def _center(self):
        self.update_idletasks()
        width, height = 1420, 880
        x = max(0, (self.winfo_screenwidth() - width) // 2)
        y = max(0, (self.winfo_screenheight() - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")


    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=236, corner_radius=0, fg_color="#0a1118")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=18, pady=(20, 22))
        ctk.CTkLabel(
            brand, text="ФСБ", width=44, height=50, corner_radius=10,
            fg_color="#1c180e", text_color=GOLD, font=font(16, "bold"),
            border_width=1, border_color="#4a3f24",
        ).pack(side="left", padx=(0, 11))
        titles = ctk.CTkFrame(brand, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "ФСБ", 19, GOLD, "bold").pack(anchor="w")
        label(titles, "ЕДИНЫЙ РЕЕСТР", 7.5, MUTED).pack(anchor="w")

        label(sidebar, "ОПЕРАТИВНАЯ РАБОТА", 8, DIM).pack(anchor="w", padx=22, pady=(6, 6))
        self.nav_registry = self._nav(sidebar, "01   Реестр записей", self.show_registry, active=True)
        self._nav(sidebar, "02   Добавить запись", self.add_client)
        self._nav(sidebar, "03   Импорт CSV / XLSX", self.import_file)
        self._nav(sidebar, "04   Экспорт реестра", self.export_file)

        label(sidebar, "КОНТРОЛЬ", 8, DIM).pack(anchor="w", padx=22, pady=(18, 6))
        self._nav(sidebar, "05   Журнал аудита", self.show_audit)
        self._nav(sidebar, "06   Обновить данные", self.refresh)

        bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=16, pady=16)
        ctk.CTkFrame(bottom, height=1, fg_color=LINE).pack(fill="x", pady=(0, 12))
        user = self.api.user
        chip = ctk.CTkFrame(bottom, fg_color="transparent")
        chip.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            chip, text=(user.get("display_name") or "?").strip()[0].upper(),
            width=32, height=32, corner_radius=8, fg_color="#1f1b10",
            text_color=GOLD, font=font(12, "bold"),
        ).pack(side="left", padx=(2, 8))
        meta = ctk.CTkFrame(chip, fg_color="transparent")
        meta.pack(side="left", fill="x", expand=True)
        label(meta, user.get("display_name") or user.get("username", "—"), 10, TEXT, "bold").pack(anchor="w")
        label(meta, user.get("role_name") or "Наблюдатель", 8.5, MUTED).pack(anchor="w")
        button(bottom, "Выйти из системы", self.logout, "ghost", 200, 32).pack(fill="x")

        main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(18, 12))
        header.grid_columnconfigure(0, weight=1)
        titles = ctk.CTkFrame(header, fg_color="transparent")
        titles.grid(row=0, column=0, sticky="w")
        label(titles, "БАЗА ДАННЫХ", 8, DIM).pack(anchor="w")
        label(titles, "Реестр записей", 24, TEXT, "bold").pack(anchor="w")

        search_box = ctk.CTkFrame(header, fg_color="transparent")
        search_box.grid(row=0, column=1, sticky="e", padx=(20, 0))
        self.search = entry(search_box, "ФИО, ИНН, СНИЛС, телефон…", 300)
        self.search.pack(side="left", padx=(0, 8))
        self.search.bind("<Return>", lambda _e: self._search_now())
        self.search.bind("<KeyRelease>", self._search_typing)
        button(search_box, "Найти", self._search_now, "ghost", 80).pack(side="left", padx=4)
        button(search_box, "+ Новая запись", self.add_client, "primary", 136).pack(side="left", padx=6)

        stats_row = ctk.CTkFrame(main, fg_color="transparent")
        stats_row.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 12))
        for index in range(4):
            stats_row.grid_columnconfigure(index, weight=1, uniform="stat")
        self.stat_labels = {}
        for index, (key, title, color) in enumerate((
            ("total", "ВСЕГО ЗАПИСЕЙ", GOLD),
            ("new_week", "НОВЫЕ ЗА 7 ДНЕЙ", GREEN),
            ("checking", "НА ПРОВЕРКЕ", CYAN),
            ("high_risk", "ВЫСОКИЙ РИСК", RED),
        )):
            box = card(stats_row, height=84)
            box.grid(row=0, column=index, sticky="ew", padx=(0 if index == 0 else 6, 0))
            box.grid_propagate(False)
            label(box, title, 8, MUTED).pack(anchor="w", padx=14, pady=(12, 0))
            value = label(box, "—", 24, color, "bold", mono=True)
            value.pack(anchor="w", padx=14, pady=(0, 8))
            self.stat_labels[key] = value

        filters = ctk.CTkFrame(main, fg_color="transparent")
        filters.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 10))
        self.status_combo = ctk.CTkComboBox(
            filters, values=[ALL_STATUS] + list(STATUS_LABELS.values()), state="readonly",
            width=150, height=32, fg_color=PANEL, border_color=LINE, button_color=PANEL_2,
            dropdown_fg_color=PANEL_2, font=font(10.5),
        )
        self.status_combo.pack(side="left", padx=(0, 6))
        self.status_combo.set(ALL_STATUS)
        self.status_combo.configure(command=lambda _v: self._load_clients(1))
        self.risk_combo = ctk.CTkComboBox(
            filters, values=[ALL_RISK] + list(RISK_LABELS.values()), state="readonly",
            width=150, height=32, fg_color=PANEL, border_color=LINE, button_color=PANEL_2,
            dropdown_fg_color=PANEL_2, font=font(10.5),
        )
        self.risk_combo.pack(side="left", padx=(0, 6))
        self.risk_combo.set(ALL_RISK)
        self.risk_combo.configure(command=lambda _v: self._load_clients(1))
        button(filters, "Сбросить", self.clear_filters, "ghost", 86, 32).pack(side="left", padx=6)
        self.total_label = label(filters, "", 9.5, DIM)
        self.total_label.pack(side="right")

        table_box = card(main)
        table_box.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 10))
        table_box.grid_columnconfigure(0, weight=1)
        table_box.grid_rowconfigure(0, weight=1)

        columns = ("fio", "birth", "status", "risk", "phone", "source", "updated")
        self.tree = ttk.Treeview(
            table_box, columns=columns, show="headings", style="FSB.Treeview", selectmode="browse"
        )
        widths = {"fio": 290, "birth": 100, "status": 110, "risk": 95, "phone": 145, "source": 150, "updated": 120}
        titles = {
            "fio": "ФИО", "birth": "Дата рождения", "status": "Статус", "risk": "Риск",
            "phone": "Телефон", "source": "Источник", "updated": "Обновлено",
        }
        for column in columns:
            self.tree.heading(column, text=titles[column], anchor="w")
            self.tree.column(column, width=widths[column], minwidth=70, anchor="w", stretch=column == "fio")
        for code, color in RISK_COLORS.items():
            self.tree.tag_configure(f"risk_{code}", foreground=color if code != "low" else TEXT)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        scroll = ttk.Scrollbar(table_box, orient="vertical", command=self.tree.yview, style="FSB.Vertical.TScrollbar")
        scroll.grid(row=0, column=1, sticky="ns", pady=8, padx=(0, 6))
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<Double-1>", lambda _e: self.open_selected())
        self.tree.bind("<Return>", lambda _e: self.open_selected())

        pager = ctk.CTkFrame(main, fg_color="transparent")
        pager.grid(row=4, column=0, sticky="ew", padx=24, pady=(0, 8))
        self.prev_btn = button(pager, "← Назад", lambda: self._load_clients(self.page - 1), "ghost", 90, 30)
        self.prev_btn.pack(side="left")
        self.page_label = label(pager, "Страница 1", 9.5, MUTED)
        self.page_label.pack(side="left", padx=12)
        self.next_btn = button(pager, "Вперёд →", lambda: self._load_clients(self.page + 1), "ghost", 90, 30)
        self.next_btn.pack(side="left")
        self.status_line = label(pager, "", 9, DIM)
        self.status_line.pack(side="right")

    def _nav(self, parent, text, command, active=False):
        btn = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            anchor="w",
            height=34,
            corner_radius=7,
            fg_color="#1a2733" if active else "transparent",
            hover_color=PANEL_2,
            text_color=GOLD if active else "#a9b7c4",
            font=font(10.5),
        )
        btn.pack(fill="x", padx=12, pady=1)
        return btn

    def show_registry(self):
        self.page = 1
        self.refresh()


    def refresh(self):
        self.load_stats()
        self._load_clients(self.page)

    def load_stats(self):
        try:
            stats = self.api.stats()
        except (ApiError, AuthExpired) as exc:
            self._status(str(exc), RED)
            return
        for key, widget in self.stat_labels.items():
            widget.configure(text=str(stats.get(key, 0)))

    def _search_typing(self, _event):
        if self.search_job:
            self.after_cancel(self.search_job)
        self.search_job = self.after(450, self._search_now)

    def _search_now(self):
        self.search_job = None
        self._load_clients(1)

    def clear_filters(self):
        self.search.delete(0, "end")
        self.status_combo.set(ALL_STATUS)
        self.risk_combo.set(ALL_RISK)
        self._load_clients(1)

    def _load_clients(self, page=1):
        page = max(1, page)
        params = {
            "search": self.search.get().strip(),
            "status": STATUS_REVERSE.get(self.status_combo.get(), ""),
            "risk_level": RISK_REVERSE.get(self.risk_combo.get(), ""),
        }
        self._status("Загрузка…", DIM)
        try:
            data = self.api.clients(page=page, page_size=PAGE_SIZE, ordering="-updated_at", **params)
        except AuthExpired:
            self._status("Сессия истекла", RED)
            self.logout()
            return
        except ApiError as exc:
            self._status(str(exc), RED)
            return

        count = data.get("count", 0)
        self.page = page
        self.pages = max(1, math.ceil(count / PAGE_SIZE))
        self.total = count
        self.tree.delete(*self.tree.get_children())
        self.rows = {}
        for client in data.get("results", []):
            iid = str(client["id"])
            self.rows[iid] = client
            self.tree.insert(
                "", "end", iid=iid,
                values=(
                    client.get("full_name") or "—",
                    fmt_date(client.get("birth_date")),
                    STATUS_LABELS.get(client.get("status"), "—"),
                    RISK_LABELS.get(client.get("risk_level"), "—"),
                    client.get("primary_phone") or client.get("phone") or "—",
                    client.get("source_name") or "Ручной ввод",
                    fmt_dt(client.get("updated_at")),
                ),
                tags=(f"risk_{client.get('risk_level')}",),
            )

        self.page_label.configure(text=f"Страница {self.page} из {self.pages}")
        self.total_label.configure(text=f"Найдено: {count}")
        self.prev_btn.configure(state="normal" if self.page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.page < self.pages else "disabled")
        self._status(f"Подключено · {self.api.base_url}  ·  Записей: {count}", GREEN)

    def _status(self, text, color=DIM):
        if hasattr(self, "status_line"):
            self.status_line.configure(text=text, text_color=color)


    def selected_id(self):
        selection = self.tree.selection()
        return int(selection[0]) if selection else None

    def add_client(self):
        ClientDialog(self, self.api, on_saved=lambda _saved: self.refresh())

    def open_selected(self):
        client_id = self.selected_id()
        if not client_id:
            messagebox.showinfo("Карточка", "Выберите запись в таблице.", parent=self)
            return
        ClientDetailWindow(self, self.api, client_id, on_changed=self.refresh)

    def delete_selected(self):
        client_id = self.selected_id()
        if not client_id:
            return
        client = self.rows.get(str(client_id), {})
        name = client.get("full_name", f"ID {client_id}")
        if not messagebox.askyesno("Архив", f"Переместить запись «{name}» в архив?", parent=self):
            return
        try:
            self.api.delete_client(client_id)
        except (ApiError, AuthExpired) as exc:
            messagebox.showerror("Ошибка", str(exc), parent=self)
            return
        self.refresh()

    def import_file(self):
        ImportDialog(self, self.api, on_done=self.refresh)

    def export_file(self):
        path = filedialog.asksaveasfilename(
            parent=self, title="Экспорт реестра", defaultextension=".csv",
            filetypes=[("CSV", "*.csv")], initialfile="fsb_clients.csv",
        )
        if not path:
            return
        params = {
            "search": self.search.get().strip(),
            "status": STATUS_REVERSE.get(self.status_combo.get(), ""),
            "risk_level": RISK_REVERSE.get(self.risk_combo.get(), ""),
        }
        try:
            response = self.api.request("GET", "clients/export/", params={k: v for k, v in params.items() if v})
            content = response.content
            with open(path, "wb") as handle:
                handle.write(content)
        except (ApiError, AuthExpired, OSError) as exc:
            messagebox.showerror("Экспорт", str(exc), parent=self)
            return
        messagebox.showinfo("Экспорт", f"Файл сохранён:\n{path}", parent=self)

    def show_audit(self):
        AuditWindow(self, self.api)

    def logout(self):
        if not messagebox.askyesno("Выход", "Завершить сеанс?", parent=self):
            return
        self.api.logout()
        self.destroy()
        self.on_logout()


if __name__ == "__main__":
    from api import ApiClient
    from config import load_config
    from login import LoginWindow
    from theme import setup_appearance

    setup_appearance()
    _cfg = load_config()
    _api = ApiClient(_cfg.get("api_base") or "http://127.0.0.1:8010/api")
    while True:
        if not _api.access:
            _login = LoginWindow(_api, _cfg)
            _login.mainloop()
            if not getattr(_login, "logged_in", False):
                break
        else:
            _main = MainWindow(_api, _cfg, on_logout=lambda: None)
            _main.mainloop()
            if _api.access:
                break

