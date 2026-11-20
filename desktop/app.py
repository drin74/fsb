"""Desktop application entry point."""
from __future__ import annotations

from api import ApiClient
from config import load_config
from login import LoginWindow
from main import MainWindow
from theme import setup_appearance


class AppController:
    def __init__(self):
        setup_appearance()
        self.config = load_config()
        self.api = ApiClient(self.config.get("api_base", "http://127.0.0.1:8010/api"))

    def run(self):
        while True:
            if not self.api.access:
                login = LoginWindow(self.api, self.config)
                login.mainloop()
                if not getattr(login, "logged_in", False):
                    break
            else:
                main = MainWindow(self.api, self.config, on_logout=lambda: None)
                main.mainloop()
                if self.api.access:
                    break


if __name__ == "__main__":
    AppController().run()
