"""HTTP client for the FSB registry REST API."""
from __future__ import annotations

import json
from pathlib import Path

import requests


class ApiError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class AuthExpired(ApiError):
    pass


def _extract_error(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"Сервер вернул {response.status_code}: {response.text[:160]}"
    if isinstance(payload, dict):
        if isinstance(payload.get("detail"), str):
            return payload["detail"]
        parts = []
        for field, value in payload.items():
            if isinstance(value, list):
                parts.append(f"{field}: {', '.join(map(str, value))}")
            elif isinstance(value, dict):
                parts.append(f"{field}: {json.dumps(value, ensure_ascii=False)}")
            else:
                parts.append(f"{field}: {value}")
        if parts:
            return "\n".join(parts)
    return str(payload)[:300]


class ApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8010/api"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self.access: str | None = None
        self.refresh: str | None = None
        self.user: dict = {}


    def login(self, username: str, password: str) -> dict:
        response = self.session.post(
            f"{self.base_url}/auth/login/",
            json={"username": username, "password": password},
            timeout=20,
        )
        if response.status_code != 200:
            raise ApiError(_extract_error(response), response.status_code)
        data = response.json()
        self.access = data["access"]
        self.refresh = data.get("refresh")
        self.user = data.get("user", {})
        self.session.headers.update({"Authorization": f"Bearer {self.access}"})
        return self.user

    def refresh_token(self) -> bool:
        if not self.refresh:
            return False
        response = self.session.post(
            f"{self.base_url}/auth/refresh/", json={"refresh": self.refresh}, timeout=20
        )
        if response.status_code != 200:
            return False
        data = response.json()
        self.access = data["access"]
        self.refresh = data.get("refresh", self.refresh)
        self.session.headers.update({"Authorization": f"Bearer {self.access}"})
        return True

    def logout(self):
        self.access = None
        self.refresh = None
        self.user = {}
        self.session.headers.pop("Authorization", None)


    def request(self, method, path, *, params=None, json_body=None, files=None, data=None, retry=True):
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            response = self.session.request(
                method, url, params=params, json=json_body, files=files, data=data, timeout=40
            )
        except requests.RequestException as exc:
            raise ApiError(f"Нет связи с сервером: {exc}") from exc

        if response.status_code == 401 and retry and self.refresh_token():
            return self.request(method, path, params=params, json_body=json_body, files=files, data=data, retry=False)
        if response.status_code == 401:
            raise AuthExpired("Сессия истекла. Войдите снова.", 401)
        if response.status_code >= 400:
            raise ApiError(_extract_error(response), response.status_code)
        if response.status_code == 204:
            return None
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return response.json()
        return response

    def get(self, path, **params):
        return self.request("GET", path, params=params)

    def post(self, path, payload=None, **extra):
        return self.request("POST", path, json_body=payload, **extra)

    def patch(self, path, payload):
        return self.request("PATCH", path, json_body=payload)

    def put(self, path, payload):
        return self.request("PUT", path, json_body=payload)

    def delete(self, path):
        return self.request("DELETE", path)


    def stats(self):
        return self.get("stats/")

    def clients(self, page=1, page_size=25, **filters):
        params = {"page": page, "page_size": page_size}
        for key, value in filters.items():
            if value:
                params[key] = value
        return self.get("clients/", **params)

    def client(self, client_id):
        return self.get(f"clients/{client_id}/")

    def create_client(self, payload):
        return self.post("clients/", payload)

    def update_client(self, client_id, payload):
        return self.patch(f"clients/{client_id}/", payload)

    def delete_client(self, client_id):
        return self.delete(f"clients/{client_id}/")

    def sources(self):
        return self.get("sources/", page_size=100)

    def audit(self, page=1, search="", action=""):
        return self.get("audit/", page=page, page_size=40, search=search, action=action)

    def users(self):
        return self.get("users/", page_size=100)

    def add_contact(self, client_id, kind, value, comment="", is_primary=False):
        return self.post("contacts/", {
            "client": client_id, "kind": kind, "value": value,
            "comment": comment, "is_primary": is_primary,
        })

    def delete_contact(self, contact_id):
        return self.delete(f"contacts/{contact_id}/")

    def add_event(self, client_id, event_type, title, description=""):
        return self.post("events/", {
            "client": client_id, "event_type": event_type,
            "title": title, "description": description,
        })

    def add_data(self, client_id, category, key, value):
        return self.post("client-data/", {
            "client": client_id, "category": category, "key": key, "value": value,
        })

    def upload_document(self, client_id, path, title, doc_type=""):
        file_path = Path(path)
        with file_path.open("rb") as handle:
            return self.post(
                "documents/",
                files={"file": (file_path.name, handle, "application/octet-stream")},
                data={"client": client_id, "title": title, "doc_type": doc_type},
            )

    def import_clients(self, file_path, source_id=None):
        file_path = Path(file_path)
        with file_path.open("rb") as handle:
            data = {"source": source_id} if source_id else {}
            return self.post(
                "clients/import/",
                files={"file": (file_path.name, handle, "application/octet-stream")},
                data=data,
            )

    def export_url(self, **filters):
        query = "&".join(f"{k}={v}" for k, v in filters.items() if v)
        return f"{self.base_url}/clients/export/?{query}"
