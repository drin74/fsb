"""Shared colors, fonts and ttk styling for the desktop client."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

BG = "#080d12"
BG_SOFT = "#0c131a"
PANEL = "#101922"
PANEL_2 = "#14202b"
PANEL_3 = "#182634"
LINE = "#21303e"
LINE_SOFT = "#192531"
TEXT = "#e7eef5"
MUTED = "#8b9aa9"
DIM = "#61717f"
GOLD = "#d8b45f"
GOLD_HOVER = "#e6c77c"
CYAN = "#5bb8d6"
GREEN = "#42b992"
AMBER = "#e0a83e"
RED = "#e1675f"

FONT = "Segoe UI"
MONO = "Consolas"

STATUS_LABELS = {
    "active": "Активен",
    "inactive": "Неактивен",
    "watch": "Наблюдение",
    "checking": "На проверке",
    "blocked": "Заблокирован",
}
STATUS_COLORS = {
    "active": GREEN,
    "inactive": MUTED,
    "watch": GOLD,
    "checking": CYAN,
    "blocked": RED,
}
RISK_LABELS = {
    "low": "Низкий",
    "medium": "Средний",
    "high": "Высокий",
    "critical": "Критический",
}
RISK_COLORS = {
    "low": GREEN,
    "medium": AMBER,
    "high": RED,
    "critical": "#c05fd0",
}
EVENT_LABELS = {
    "update": "Обновление",
    "check": "Проверка",
    "incident": "Инцидент",
    "request": "Запрос",
    "import": "Импорт",
    "note": "Заметка",
}


def setup_appearance():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")


def configure_treeview_style():
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure(
        "FSB.Treeview",
        background=PANEL,
        fieldbackground=PANEL,
        foreground=TEXT,
        borderwidth=0,
        rowheight=34,
        font=(FONT, 10),
    )
    style.configure(
        "FSB.Treeview.Heading",
        background=PANEL_2,
        foreground=MUTED,
        borderwidth=0,
        relief="flat",
        font=(FONT, 8, "bold"),
        padding=(6, 8),
    )
    style.map(
        "FSB.Treeview",
        background=[("selected", "#1e3346")],
        foreground=[("selected", "#ffffff")],
    )
    style.map("FSB.Treeview.Heading", background=[("active", PANEL_3)])
    style.configure(
        "FSB.Vertical.TScrollbar",
        background=PANEL_2,
        troughcolor=PANEL,
        borderwidth=0,
        arrowsize=0,
        relief="flat",
        width=10,
    )


def font(size=12, weight="normal", mono=False):
    return (MONO if mono else FONT, size, weight)


def entry(parent, placeholder="", width=200, show=None):
    return ctk.CTkEntry(
        parent,
        width=width,
        height=34,
        corner_radius=7,
        border_width=1,
        border_color=LINE,
        fg_color="#0b131a",
        text_color=TEXT,
        placeholder_text=placeholder,
        placeholder_text_color="#4d5f6e",
        font=font(11),
        show=show,
    )


def button(parent, text, command, kind="ghost", width=120, height=34):
    colors = {
        "primary": (GOLD, "#171208", GOLD_HOVER),
        "ghost": (PANEL_2, MUTED, PANEL_3),
        "danger": ("#2a1517", "#f0a09a", "#3a1b1e"),
        "cyan": ("#10262f", "#a9e0f0", "#163441"),
    }
    fg, text_color, hover = colors.get(kind, colors["ghost"])
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=height,
        corner_radius=7,
        fg_color=fg,
        hover_color=hover,
        text_color=text_color,
        border_width=0 if kind == "primary" else 1,
        border_color=LINE,
        font=font(11, "bold"),
    )


def label(parent, text, size=11, color=TEXT, weight="normal", mono=False, **kwargs):
    return ctk.CTkLabel(
        parent, text=text, text_color=color, font=font(size, weight, mono), anchor="w", **kwargs
    )


def card(parent, **kwargs):
    return ctk.CTkFrame(
        parent,
        fg_color=PANEL,
        corner_radius=12,
        border_width=1,
        border_color=LINE,
        **kwargs,
    )


def separator(parent):
    return ctk.CTkFrame(parent, height=1, fg_color=LINE_SOFT)
