"""Client detail window with contacts, events and documents."""
from __future__ import annotations

import datetime as dt
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import webbrowser

import customtkinter as ctk

from api import ApiClient, ApiError, AuthExpired
from client_form import ClientDialog
from theme import (
    AMBER,
    BG,
    CYAN,
    DIM,
    EVENT_LABELS,
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
    entry,
    font,
    label,
)

KIND_LABELS = {"phone": "Телефон", "email": "Email", "telegram": "Telegram", "whatsapp": "WhatsApp", "other": "Другое"}
KIND_REVERSE = {v: k for k, v in KIND_LABELS.items()}
CONTACT_KINDS = list(KIND_LABELS.values())


def fmt_dt(value):
    if not value:
        return "—"
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return value


def fmt_date(value):
    if not value:
        return "—"
    try:
        return dt.date.fromisoformat(value[:10]).strftime("%d.%m.%Y")
    except ValueError:
        return value


class ClientDetailWindow(ctk.CTkToplevel):
    def __init__(self, master, api: ApiClient, client_id: int, on_changed=None):
        super().__init__(master)
        self.api = api
        self.client_id = client_id
        self.client: dict = {}
        self.on_changed = on_changed

        self.title("Карточка записи")
        self.geometry("1040x820")
        self.minsize(900, 700)
        self.configure(fg_color=BG)
        self.transient(master)

        self.header = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0)
        self.header.pack(fill="x")
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=18, pady=14)

        self.tabview = ctk.CTkTabview(
            self.body,
            fg_color=PANEL,
            segmented_button_fg_color=PANEL_2,
            segmented_button_selected_color="#2a3a49",
            segmented_button_selected_hover_color="#31465a",
            segmented_button_unselected_color=PANEL_2,
            text_color=TEXT,
            border_width=1,
            border_color=LINE,
            corner_radius=12,
        )
        self.tabview.pack(fill="both", expand=True)
        self.tab_info = self.tabview.add("Анкета")
        self.tab_contacts = self.tabview.add("Контакты")
        self.tab_events = self.tabview.add("События")
        self.tab_docs = self.tabview.add("Документы")

        self.load()


    def load(self):
        try:
            self.client = self.api.client(self.client_id)
        except AuthExpired:
            messagebox.showerror("Сессия", "Сессия истекла. Войдите снова.", parent=self)
            self.destroy()
            return
        except ApiError as exc:
            messagebox.showerror("Ошибка", str(exc), parent=self)
            self.destroy()
            return
        self._render_header()
        self._render_info()
        self._render_contacts()
        self._render_events()
        self._render_documents()

    def _clear(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def _render_header(self):
        self._clear(self.header)
        client = self.client
        inner = ctk.CTkFrame(self.header, fg_color="transparent")
        inner.pack(fill="x", padx=22, pady=16)

        avatar = ctk.CTkLabel(
            inner,
            text=f"{(client.get('last_name') or ' ')[0]}{(client.get('first_name') or ' ')[0]}".upper(),
            width=62,
            height=62,
            corner_radius=12,
            fg_color="#1f1b10",
            text_color=GOLD,
            font=font(20, "bold"),
        )
        avatar.pack(side="left", padx=(0, 16))

        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        badges = ctk.CTkFrame(info, fg_color="transparent")
        badges.pack(anchor="w", pady=(0, 3))
        self._badge(badges, STATUS_LABELS.get(client.get("status"), "—"), STATUS_COLORS.get(client.get("status"), MUTED))
        self._badge(badges, "Риск: " + RISK_LABELS.get(client.get("risk_level"), "—"), RISK_COLORS.get(client.get("risk_level"), MUTED))
        label(info, client.get("full_name") or "Без имени", 20, TEXT, "bold").pack(anchor="w")
        meta = f"ID {client.get('id')} · {client.get('gender_display') or 'пол не указан'} · {fmt_date(client.get('birth_date'))}"
        if client.get("age"):
            meta += f" · {client['age']} лет"
        label(info, meta, 10.5, MUTED).pack(anchor="w")

        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(side="right")
        button(actions, "Изменить", self.edit, "primary", 100).pack(side="left", padx=4)
        button(actions, "В архив", self.delete, "danger", 100).pack(side="left", padx=4)
        button(actions, "Закрыть", self.destroy, "ghost", 90).pack(side="left", padx=4)

    def _badge(self, parent, text, color):
        ctk.CTkLabel(
            parent,
            text=text,
            height=20,
            corner_radius=4,
            fg_color="#111a23",
            text_color=color,
            font=font(9, "bold"),
            padx=8,
        ).pack(side="left", padx=(0, 6))

    def _render_info(self):
        frame = self.tab_info
        self._clear(frame)
        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)
        scroll.grid_columnconfigure((0, 1), weight=1, uniform="info")

        facts = [
            ("Дата рождения", fmt_date(self.client.get("birth_date"))),
            ("Гражданство", self.client.get("citizenship") or "—"),
            ("ИНН", self.client.get("inn") or "—"),
            ("СНИЛС", self.client.get("snils") or "—"),
            ("Паспорт", f"{self.client.get('passport_series') or ''} {self.client.get('passport_number') or ''}".strip() or "—"),
            ("Кем выдан", self.client.get("passport_issued_by") or "—"),
            ("Дата выдачи", fmt_date(self.client.get("passport_issue_date"))),
            ("Телефон", self.client.get("phone") or "—"),
            ("Email", self.client.get("email") or "—"),
            ("Источник", self.client.get("source_name") or "Ручной ввод"),
            ("Создано", fmt_dt(self.client.get("created_at"))),
            ("Автор", self.client.get("created_by_name") or "система"),
        ]
        for index, (key, value) in enumerate(facts):
            holder = ctk.CTkFrame(scroll, fg_color="transparent")
            holder.grid(row=index // 2, column=index % 2, sticky="ew", padx=10, pady=5)
            label(holder, key.upper(), 8.5, DIM).pack(anchor="w")
            label(holder, str(value), 11.5, TEXT).pack(anchor="w")

        for title, key in (("Адрес регистрации", "address_registration"), ("Адрес проживания", "address_actual")):
            holder = ctk.CTkFrame(scroll, fg_color="transparent")
            holder.grid(row=6 + (key == "address_actual"), column=0, columnspan=2, sticky="ew", padx=10, pady=5)
            label(holder, title.upper(), 8.5, DIM).pack(anchor="w")
            label(holder, self.client.get(key) or "—", 11.5, TEXT, wraplength=760, justify="left").pack(anchor="w")

        notes = ctk.CTkFrame(scroll, fg_color=PANEL_2, corner_radius=8)
        notes.grid(row=10, column=0, columnspan=2, sticky="ew", padx=10, pady=(14, 4))
        label(notes, "ПРИМЕЧАНИЯ", 8.5, GOLD, "bold").pack(anchor="w", padx=12, pady=(10, 2))
        label(notes, self.client.get("notes") or "Нет примечаний", 10.5, MUTED, wraplength=740, justify="left").pack(anchor="w", padx=12, pady=(0, 10))

        tags = self.client.get("tag_list") or []
        if tags:
            tag_row = ctk.CTkFrame(scroll, fg_color="transparent")
            tag_row.grid(row=11, column=0, columnspan=2, sticky="w", padx=10, pady=8)
            for tag in tags:
                ctk.CTkLabel(tag_row, text=tag, height=22, corner_radius=4, fg_color=PANEL_2, text_color=MUTED, font=font(9)).pack(side="left", padx=3)

    def _render_contacts(self):
        frame = self.tab_contacts
        self._clear(frame)
        list_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent", height=420)
        list_frame.pack(fill="both", expand=True, padx=4, pady=(4, 8))

        contacts = self.client.get("contacts") or []
        if not contacts:
            label(list_frame, "Контакты не добавлены.", 11, MUTED).pack(anchor="w", padx=8, pady=10)
        for contact in contacts:
            row = ctk.CTkFrame(list_frame, fg_color=PANEL_2, corner_radius=7)
            row.pack(fill="x", pady=3)
            label(row, KIND_LABELS.get(contact.get("kind"), contact.get("kind")), 9, DIM).pack(side="left", padx=12, pady=9)
            label(row, contact.get("value", ""), 11.5, TEXT, "bold").pack(side="left", padx=8)
            if contact.get("is_primary"):
                label(row, "основной", 8.5, GOLD).pack(side="left", padx=6)
            button(row, "Удалить", lambda cid=contact["id"]: self._delete_contact(cid), "danger", 76, 26).pack(side="right", padx=8, pady=5)

        form = ctk.CTkFrame(frame, fg_color=PANEL_2, corner_radius=9)
        form.pack(fill="x", padx=4, pady=(0, 4))
        label(form, "ДОБАВИТЬ КОНТАКТ", 8.5, GOLD, "bold").grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(10, 6))
        self.contact_kind = ctk.CTkComboBox(form, values=CONTACT_KINDS, state="readonly", width=120, height=32, fg_color="#0b131a", border_color=LINE, button_color=PANEL_3, dropdown_fg_color=PANEL, font=font(10))
        self.contact_kind.grid(row=1, column=0, padx=(12, 6), pady=(0, 12))
        self.contact_value = entry(form, "Телефон, email или ник", 260)
        self.contact_value.grid(row=1, column=1, sticky="ew", padx=6, pady=(0, 12))
        form.grid_columnconfigure(1, weight=1)
        button(form, "Добавить", self._add_contact, "cyan", 100, 32).grid(row=1, column=2, padx=(6, 12), pady=(0, 12))

    def _render_events(self):
        frame = self.tab_events
        self._clear(frame)
        list_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent", height=430)
        list_frame.pack(fill="both", expand=True, padx=4, pady=(4, 8))

        events = self.client.get("events") or []
        if not events:
            label(list_frame, "Событий пока нет.", 11, MUTED).pack(anchor="w", padx=8, pady=10)
        for event in events[:40]:
            row = ctk.CTkFrame(list_frame, fg_color=PANEL_2, corner_radius=7)
            row.pack(fill="x", pady=3)
            color = {"incident": RED, "check": CYAN, "import": GREEN, "request": AMBER}.get(event.get("event_type"), GOLD)
            label(row, EVENT_LABELS.get(event.get("event_type"), "—").upper(), 8, color, "bold").pack(anchor="w", padx=12, pady=(8, 0))
            label(row, event.get("title", ""), 11.5, TEXT, "bold").pack(anchor="w", padx=12)
            if event.get("description"):
                label(row, event["description"], 10, MUTED, wraplength=820, justify="left").pack(anchor="w", padx=12)
            label(row, f"{fmt_dt(event.get('occurred_at'))} · {event.get('created_by_name') or 'система'}", 9, DIM).pack(anchor="w", padx=12, pady=(2, 8))

        form = ctk.CTkFrame(frame, fg_color=PANEL_2, corner_radius=9)
        form.pack(fill="x", padx=4)
        label(form, "ДОБАВИТЬ СОБЫТИЕ", 8.5, GOLD, "bold").grid(row=0, column=0, columnspan=3, sticky="w", padx=12, pady=(10, 6))
        self.event_type = ctk.CTkComboBox(form, values=list(EVENT_LABELS.values()), state="readonly", width=130, height=32, fg_color="#0b131a", border_color=LINE, button_color=PANEL_3, dropdown_fg_color=PANEL, font=font(10))
        self.event_type.grid(row=1, column=0, padx=(12, 6), pady=(0, 12))
        self.event_title = entry(form, "Заголовок события", 380)
        self.event_title.grid(row=1, column=1, sticky="ew", padx=6, pady=(0, 12))
        form.grid_columnconfigure(1, weight=1)
        button(form, "Добавить", self._add_event, "cyan", 100, 32).grid(row=1, column=2, padx=(6, 12), pady=(0, 12))

    def _render_documents(self):
        frame = self.tab_docs
        self._clear(frame)
        top = ctk.CTkFrame(frame, fg_color="transparent")
        top.pack(fill="x", padx=4, pady=(4, 8))
        label(top, "Документы карточки", 12, TEXT, "bold").pack(side="left")
        button(top, "Загрузить файл", self._upload_document, "cyan", 130).pack(side="right")

        list_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=4)
        documents = self.client.get("documents") or []
        if not documents:
            label(list_frame, "Документы не загружены.", 11, MUTED).pack(anchor="w", padx=8, pady=10)
        for document in documents:
            row = ctk.CTkFrame(list_frame, fg_color=PANEL_2, corner_radius=7)
            row.pack(fill="x", pady=3)
            label(row, "FILE", 8, RED, "bold", mono=True).pack(side="left", padx=12)
            box = ctk.CTkFrame(row, fg_color="transparent")
            box.pack(side="left", fill="x", expand=True, padx=6, pady=8)
            label(box, document.get("title", ""), 11.5, TEXT, "bold").pack(anchor="w")
            label(box, f"{document.get('doc_type') or 'документ'} · {fmt_dt(document.get('uploaded_at'))}", 9, DIM).pack(anchor="w")
            if document.get("file_url"):
                button(row, "Открыть", lambda url=document["file_url"]: webbrowser.open(url), "ghost", 82, 28).pack(side="right", padx=8)


    def edit(self):
        ClientDialog(self.master, self.api, on_saved=self._on_saved, client=self.client)

    def _on_saved(self, _saved=None):
        self.load()
        if self.on_changed:
            self.on_changed()

    def delete(self):
        if not messagebox.askyesno("Архив", "Переместить запись в архив?", parent=self):
            return
        try:
            self.api.delete_client(self.client_id)
        except ApiError as exc:
            messagebox.showerror("Ошибка", str(exc), parent=self)
            return
        if self.on_changed:
            self.on_changed()
        self.destroy()

    def _delete_contact(self, contact_id):
        try:
            self.api.delete_contact(contact_id)
        except ApiError as exc:
            messagebox.showerror("Ошибка", str(exc), parent=self)
            return
        self.load()

    def _add_contact(self):
        value = self.contact_value.get().strip()
        if not value:
            messagebox.showwarning("Контакт", "Введите значение контакта.", parent=self)
            return
        try:
            self.api.add_contact(self.client_id, KIND_REVERSE[self.contact_kind.get()], value)
        except ApiError as exc:
            messagebox.showerror("Ошибка", str(exc), parent=self)
            return
        self.contact_value.delete(0, "end")
        self.load()

    def _add_event(self):
        title = self.event_title.get().strip()
        if not title:
            messagebox.showwarning("Событие", "Введите заголовок события.", parent=self)
            return
        reverse = {v: k for k, v in EVENT_LABELS.items()}
        try:
            self.api.add_event(self.client_id, reverse.get(self.event_type.get(), "note"), title)
        except ApiError as exc:
            messagebox.showerror("Ошибка", str(exc), parent=self)
            return
        self.event_title.delete(0, "end")
        self.load()

    def _upload_document(self):
        path = filedialog.askopenfilename(parent=self, title="Выберите документ")
        if not path:
            return
        from pathlib import Path

        file_path = Path(path)
        try:
            self.api.upload_document(self.client_id, path, file_path.stem, file_path.suffix.lstrip(".").upper())
        except ApiError as exc:
            messagebox.showerror("Ошибка", str(exc), parent=self)
            return
        self.load()
