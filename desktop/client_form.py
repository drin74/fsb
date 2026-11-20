"""Create / edit client dialog."""
from __future__ import annotations

import datetime as dt
import tkinter.messagebox as messagebox

import customtkinter as ctk

from api import ApiClient, ApiError, AuthExpired
from theme import (
    BG,
    CYAN,
    DIM,
    GOLD,
    LINE,
    MUTED,
    PANEL,
    PANEL_2,
    PANEL_3,
    RED,
    RISK_LABELS,
    STATUS_LABELS,
    TEXT,
    button,
    entry,
    font,
    label,
)

GENDER_MAP = {"Мужской": "M", "Женский": "F", "": ""}
GENDER_REVERSE = {"M": "Мужской", "F": "Женский", "": ""}
STATUS_REVERSE = {v: k for k, v in STATUS_LABELS.items()}
RISK_REVERSE = {v: k for k, v in RISK_LABELS.items()}


def to_iso(value: str):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Некорректная дата: {value}. Используйте ДД.ММ.ГГГГ")


def from_iso(value):
    if not value:
        return ""
    try:
        return dt.date.fromisoformat(value[:10]).strftime("%d.%m.%Y")
    except ValueError:
        return value


class ClientDialog(ctk.CTkToplevel):
    def __init__(self, master, api: ApiClient, on_saved, client: dict | None = None):
        super().__init__(master)
        self.api = api
        self.on_saved = on_saved
        self.client = client
        self.sources: list[dict] = []
        self.source_map: dict[str, int] = {}
        self.entries: dict[str, ctk.CTkEntry] = {}
        self.combos: dict[str, ctk.CTkComboBox] = {}
        self.busy = False

        self.title("Редактирование записи" if client else "Новая запись")
        self.geometry("940x780")
        self.minsize(820, 640)
        self.configure(fg_color=BG)
        self.transient(master)
        self.grab_set()

        self._build()
        self._load_sources()
        if client:
            self._fill(client)


    def _build(self):
        header = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=74)
        header.pack(fill="x")
        header.pack_propagate(False)
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", padx=24, pady=14)
        label(left, "РЕЕСТР ЗАПИСЕЙ", 9, GOLD, "bold").pack(anchor="w")
        label(left, self.title(), 19, TEXT, "bold").pack(anchor="w")
        button(header, "Закрыть", self.destroy, "ghost", 90).pack(side="right", padx=20)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll.pack(fill="both", expand=True, padx=18, pady=14)
        self.scroll.grid_columnconfigure((0, 1), weight=1, uniform="form")

        self.form_row = 0
        self.form_col = 0
        self._section("Идентификация")
        self._field("last_name", "Фамилия *")
        self._field("first_name", "Имя *")
        self._field("middle_name", "Отчество")
        self._field("birth_date", "Дата рождения (ДД.ММ.ГГГГ)")
        self._combo("gender", "Пол", ["", "Мужской", "Женский"])
        self._field("citizenship", "Гражданство", default="РФ")

        self._section("Документы и реквизиты")
        self._field("inn", "ИНН")
        self._field("snils", "СНИЛС")
        self._field("passport_series", "Серия паспорта")
        self._field("passport_number", "Номер паспорта")
        self._field("passport_issued_by", "Кем выдан")
        self._field("passport_issue_date", "Дата выдачи (ДД.ММ.ГГГГ)")

        self._section("Контакты и адреса")
        self._field("phone", "Телефон")
        self._field("email", "Email")
        self._field("address_registration", "Адрес регистрации", wide=True)
        self._field("address_actual", "Адрес проживания", wide=True)

        self._section("Учёт и контроль")
        self._combo("status", "Статус", list(STATUS_LABELS.values()))
        self._combo("risk_level", "Уровень риска", list(RISK_LABELS.values()))
        self._combo("source", "Источник", ["— не указан —"])
        self._field("tags", "Метки (через запятую)")
        self._field("notes", "Примечания", wide=True, height=76)

        footer = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0)
        footer.pack(fill="x", side="bottom")
        self.error_label = label(footer, "", 10.5, RED)
        self.error_label.pack(side="left", padx=22, pady=12)
        self.save_btn = button(footer, "Сохранить", self._save, "primary", 150, 38)
        self.save_btn.pack(side="right", padx=18, pady=12)
        button(footer, "Отмена", self.destroy, "ghost", 100, 38).pack(side="right", padx=6, pady=12)

    def _section(self, title: str):
        if self.form_col == 1:
            self.form_row += 1
            self.form_col = 0
        frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        frame.grid(row=self.form_row, column=0, columnspan=2, sticky="ew", pady=(14 if self.form_row else 0, 4))
        label(frame, title.upper(), 9, GOLD, "bold").pack(anchor="w")
        ctk.CTkFrame(frame, height=1, fg_color=LINE).pack(fill="x", pady=(5, 0))
        self.form_row += 1

    def _next_pos(self, wide: bool):
        if wide:
            if self.form_col == 1:
                self.form_row += 1
                self.form_col = 0
            pos = (self.form_row, 0)
            self.form_row += 1
            return pos
        pos = (self.form_row, self.form_col)
        if self.form_col == 0:
            self.form_col = 1
        else:
            self.form_col = 0
            self.form_row += 1
        return pos

    def _field(self, name, caption, wide=False, default="", height=34):
        row, col = self._next_pos(wide)
        holder = ctk.CTkFrame(self.scroll, fg_color="transparent")
        holder.grid(
            row=row,
            column=col,
            columnspan=2 if wide else 1,
            sticky="ew",
            padx=(0, 8) if col == 0 and not wide else ((8, 0) if col == 1 else 0),
            pady=4,
        )
        label(holder, caption, 9.5, MUTED).pack(anchor="w", pady=(0, 3))
        widget = entry(holder, width=300)
        widget.configure(height=height)
        widget.pack(fill="x")
        if default:
            widget.insert(0, default)
        self.entries[name] = widget

    def _combo(self, name, caption, values):
        row, col = self._next_pos(False)
        holder = ctk.CTkFrame(self.scroll, fg_color="transparent")
        holder.grid(
            row=row,
            column=col,
            sticky="ew",
            padx=(0, 8) if col == 0 else (8, 0),
            pady=4,
        )
        label(holder, caption, 9.5, MUTED).pack(anchor="w", pady=(0, 3))
        combo = ctk.CTkComboBox(
            holder,
            values=values,
            height=34,
            corner_radius=7,
            border_width=1,
            border_color=LINE,
            fg_color="#0b131a",
            button_color=PANEL_2,
            button_hover_color=PANEL_3,
            dropdown_fg_color=PANEL_2,
            dropdown_hover_color=PANEL_3,
            text_color=TEXT,
            font=font(11),
            dropdown_font=font(11),
            state="readonly",
        )
        combo.set(values[0] if values else "")
        combo.pack(fill="x")
        self.combos[name] = combo


    def _load_sources(self):
        try:
            data = self.api.sources()
            self.sources = data.get("results", [])
        except ApiError:
            self.sources = []
        names = ["— не указан —"] + [s["name"] for s in self.sources]
        self.source_map = {s["name"]: s["id"] for s in self.sources}
        self.combos["source"].configure(values=names)
        if self.combos["source"].get() not in names:
            self.combos["source"].set(names[0])

    def _fill(self, client: dict):
        simple = [
            "last_name", "first_name", "middle_name", "citizenship", "inn", "snils",
            "passport_series", "passport_number", "passport_issued_by", "phone",
            "email", "address_registration", "address_actual", "tags", "notes",
        ]
        for key in simple:
            self.entries[key].delete(0, "end")
            self.entries[key].insert(0, client.get(key) or "")
        self.entries["birth_date"].insert(0, from_iso(client.get("birth_date")))
        self.entries["passport_issue_date"].insert(0, from_iso(client.get("passport_issue_date")))
        self.combos["gender"].set(GENDER_REVERSE.get(client.get("gender") or "", ""))
        self.combos["status"].set(STATUS_LABELS.get(client.get("status"), "Активен"))
        self.combos["risk_level"].set(RISK_LABELS.get(client.get("risk_level"), "Низкий"))
        source_name = client.get("source_name")
        if source_name and source_name in self.source_map:
            self.combos["source"].set(source_name)
        else:
            self.combos["source"].set("— не указан —")

    def _payload(self) -> dict:
        last_name = self.entries["last_name"].get().strip()
        first_name = self.entries["first_name"].get().strip()
        if not last_name or not first_name:
            raise ValueError("Заполните фамилию и имя.")
        source_name = self.combos["source"].get()
        return {
            "last_name": last_name,
            "first_name": first_name,
            "middle_name": self.entries["middle_name"].get().strip(),
            "birth_date": to_iso(self.entries["birth_date"].get()),
            "gender": GENDER_MAP.get(self.combos["gender"].get(), ""),
            "citizenship": self.entries["citizenship"].get().strip() or "РФ",
            "inn": self.entries["inn"].get().strip(),
            "snils": self.entries["snils"].get().strip(),
            "passport_series": self.entries["passport_series"].get().strip(),
            "passport_number": self.entries["passport_number"].get().strip(),
            "passport_issued_by": self.entries["passport_issued_by"].get().strip(),
            "passport_issue_date": to_iso(self.entries["passport_issue_date"].get()),
            "phone": self.entries["phone"].get().strip(),
            "email": self.entries["email"].get().strip(),
            "address_registration": self.entries["address_registration"].get().strip(),
            "address_actual": self.entries["address_actual"].get().strip(),
            "status": STATUS_REVERSE.get(self.combos["status"].get(), "active"),
            "risk_level": RISK_REVERSE.get(self.combos["risk_level"].get(), "low"),
            "source": self.source_map.get(source_name),
            "tags": self.entries["tags"].get().strip(),
            "notes": self.entries["notes"].get().strip(),
        }

    def _save(self):
        if self.busy:
            return
        try:
            payload = self._payload()
        except ValueError as exc:
            self.error_label.configure(text=str(exc))
            return
        self.busy = True
        self.save_btn.configure(state="disabled", text="Сохранение…")
        try:
            if self.client:
                saved = self.api.update_client(self.client["id"], payload)
            else:
                saved = self.api.create_client(payload)
            self.on_saved(saved)
            self.destroy()
        except AuthExpired:
            messagebox.showerror("Сессия", "Сессия истекла. Войдите снова.", parent=self)
            self.destroy()
        except (ApiError, ValueError) as exc:
            self.error_label.configure(text=str(exc)[:300])
        finally:
            self.busy = False
            if self.winfo_exists():
                self.save_btn.configure(state="normal", text="Сохранить")
