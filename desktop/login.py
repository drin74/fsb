"""Login screen for the desktop client."""
from __future__ import annotations

import customtkinter as ctk

from api import ApiClient, ApiError
from config import save_config
from theme import (
    BG,
    CYAN,
    DIM,
    GOLD,
    GREEN,
    LINE,
    LINE_SOFT,
    MUTED,
    PANEL,
    PANEL_2,
    RED,
    TEXT,
    button,
    entry,
    font,
    label,
)


class LoginWindow(ctk.CTk):
    def __init__(self, api: ApiClient, config: dict):
        super().__init__()
        self.api = api
        self.config = config
        self.logged_in = False
        self.busy = False

        self.title("ФСБ · Единый реестр — вход")
        self.geometry("1040x640")
        self.minsize(900, 600)
        self.configure(fg_color=BG)
        self._center(1040, 640)

        self._build()

    def _center(self, width, height):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build(self):
        shell = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0)
        shell.pack(fill="both", expand=True)


        left = ctk.CTkFrame(shell, fg_color="#0a1118", corner_radius=0, width=560)
        left.pack(side="left", fill="both", expand=True)
        left.pack_propagate(False)

        top = ctk.CTkFrame(left, fg_color="transparent")
        top.pack(fill="x", padx=40, pady=(36, 0))
        emblem = ctk.CTkLabel(
            top,
            text="ФСБ",
            width=56,
            height=64,
            corner_radius=12,
            fg_color="#1c180e",
            text_color=GOLD,
            font=font(20, "bold"),
            border_width=1,
            border_color="#4a3f24",
        )
        emblem.pack(side="left", padx=(0, 14))
        titles = ctk.CTkFrame(top, fg_color="transparent")
        titles.pack(side="left")
        label(titles, "ФСБ", 24, GOLD, "bold").pack(anchor="w")
        label(titles, "ЕДИНЫЙ РЕЕСТР", 9, MUTED).pack(anchor="w")

        body = ctk.CTkFrame(left, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=40, pady=(60, 0))
        label(body, "ЗАЩИЩЁННЫЙ КОНТУР · СЛУЖЕБНЫЙ ДОСТУП", 8.5, GOLD, "bold").pack(anchor="w")
        label(body, "Единая система\nучёта и обработки\nданных", 34, TEXT, "bold", justify="left").pack(anchor="w", pady=(10, 14))
        label(
            body,
            "Настольный клиент работает с общей базой\nMySQL через REST API. Все действия\nфиксируются в журнале аудита.",
            11.5,
            MUTED,
            justify="left",
        ).pack(anchor="w")

        features = ctk.CTkFrame(body, fg_color="transparent")
        features.pack(anchor="w", pady=(28, 0))
        for number, text in (("01", "Карточки и связи"), ("02", "Импорт CSV / XLSX"), ("03", "Полный аудит")):
            row = ctk.CTkFrame(features, fg_color=PANEL_2, corner_radius=6)
            row.pack(anchor="w", pady=3)
            label(row, number, 8.5, GOLD, mono=True).pack(side="left", padx=(10, 7), pady=6)
            label(row, text, 10.5, TEXT).pack(side="left", padx=(0, 12))

        label(left, "●  СОЕДИНЕНИЕ ЗАЩИЩЕНО · TLS В ПРОМЫШЛЕННОМ КОНТУРЕ", 8, DIM).pack(anchor="w", side="bottom", padx=40, pady=26)


        right = ctk.CTkFrame(shell, fg_color="#090e14", corner_radius=0, width=460)
        right.pack(side="right", fill="both")
        right.pack_propagate(False)

        form = ctk.CTkFrame(right, fg_color="transparent")
        form.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.78)

        label(form, "ИДЕНТИФИКАЦИЯ", 8.5, GOLD, "bold").pack(anchor="w")
        label(form, "Вход в систему", 24, TEXT, "bold").pack(anchor="w", pady=(4, 3))
        label(form, "Используйте служебную учётную запись", 10.5, MUTED).pack(anchor="w", pady=(0, 18))

        label(form, "СЕРВЕР API", 8.5, MUTED).pack(anchor="w", pady=(0, 3))
        self.api_entry = entry(form, "http://127.0.0.1:8010/api", 330)
        self.api_entry.insert(0, self.config.get("api_base", "http://127.0.0.1:8010/api"))
        self.api_entry.pack(fill="x", pady=(0, 11))

        label(form, "ЛОГИН", 8.5, MUTED).pack(anchor="w", pady=(0, 3))
        self.username = entry(form, "admin", 330)
        self.username.insert(0, self.config.get("remember_username", "admin"))
        self.username.pack(fill="x", pady=(0, 11))

        label(form, "ПАРОЛЬ", 8.5, MUTED).pack(anchor="w", pady=(0, 3))
        self.password = entry(form, "••••••••", 330, show="•")
        self.password.pack(fill="x", pady=(0, 16))
        self.password.bind("<Return>", lambda _e: self.login())
        self.username.bind("<Return>", lambda _e: self.password.focus_set())
        self.api_entry.bind("<Return>", lambda _e: self.username.focus_set())

        self.login_btn = button(form, "Войти в реестр", self.login, "primary", 330, 40)
        self.login_btn.pack(fill="x")
        self.error = label(form, "", 10, RED, wraplength=320, justify="left")
        self.error.pack(anchor="w", pady=(10, 0))

        divider = ctk.CTkFrame(form, height=1, fg_color=LINE)
        divider.pack(fill="x", pady=(22, 12))
        label(form, "ДЕМОНСТРАЦИОННЫЕ УЧЁТНЫЕ ЗАПИСИ", 8, DIM).pack(anchor="w", pady=(0, 5))
        for login, password, role in (
            ("admin", "Admin123!", "администратор"),
            ("operator", "Operator123!", "оператор"),
            ("analyst", "Analyst123!", "аналитик"),
        ):
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", pady=1)
            label(row, login, 9.5, GOLD, mono=True, width=70).pack(side="left")
            label(row, password, 9.5, MUTED, mono=True).pack(side="left", padx=8)
            label(row, role, 8, DIM).pack(side="right")

        label(right, "© 2026 · УЧЕБНЫЙ ДЕМОНСТРАЦИОННЫЙ СТЕНД", 8, DIM).pack(side="bottom", pady=20)

    def login(self):
        if self.busy:
            return
        base = self.api_entry.get().strip().rstrip("/")
        username = self.username.get().strip()
        password = self.password.get()
        if not base or not username or not password:
            self.error.configure(text="Заполните адрес API, логин и пароль.")
            return
        self.busy = True
        self.login_btn.configure(state="disabled", text="Проверка доступа…")
        self.error.configure(text="")
        self.api.base_url = base
        try:
            self.api.login(username, password)
        except ApiError as exc:
            self.error.configure(text=str(exc)[:220])
            self.busy = False
            self.login_btn.configure(state="normal", text="Войти в реестр")
            return

        self.config["api_base"] = base
        self.config["remember_username"] = username
        save_config(self.config)
        self.busy = False
        self.logged_in = True
        self.destroy()
