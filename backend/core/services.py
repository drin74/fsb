import csv
import datetime as dt
import io
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from .models import AuditLog, Client, ClientContact, DataEvent, DataSource


def client_ip(request):
    if not request:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(request, action, obj=None, model_name="", details=None, actor=None):
    user = actor
    if user is None:
        user = getattr(request, "user", None)
    if user is not None and not getattr(user, "is_authenticated", False):
        user = None
    return AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name or (obj.__class__.__name__ if obj is not None else ""),
        object_id=str(getattr(obj, "pk", "") or ""),
        object_repr=str(obj)[:255] if obj is not None else "",
        details=details or {},
        ip=client_ip(request),
    )


STATUS_MAP = {
    "активен": Client.Status.ACTIVE,
    "активный": Client.Status.ACTIVE,
    "active": Client.Status.ACTIVE,
    "неактивен": Client.Status.INACTIVE,
    "inactive": Client.Status.INACTIVE,
    "наблюдение": Client.Status.WATCH,
    "watch": Client.Status.WATCH,
    "на проверке": Client.Status.CHECKING,
    "проверка": Client.Status.CHECKING,
    "checking": Client.Status.CHECKING,
    "заблокирован": Client.Status.BLOCKED,
    "blocked": Client.Status.BLOCKED,
}

RISK_MAP = {
    "низкий": Client.Risk.LOW,
    "low": Client.Risk.LOW,
    "средний": Client.Risk.MEDIUM,
    "medium": Client.Risk.MEDIUM,
    "высокий": Client.Risk.HIGH,
    "high": Client.Risk.HIGH,
    "критический": Client.Risk.CRITICAL,
    "critical": Client.Risk.CRITICAL,
}

HEADER_ALIASES = {
    "last_name": {"фамилия", "last_name", "surname", "family"},
    "first_name": {"имя", "first_name", "name"},
    "middle_name": {"отчество", "middle_name", "patronymic"},
    "birth_date": {"дата рождения", "дата_рождения", "др", "birth_date", "birthday"},
    "gender": {"пол", "gender", "sex"},
    "citizenship": {"гражданство", "citizenship"},
    "inn": {"инн", "inn"},
    "snils": {"снилс", "snils"},
    "phone": {"телефон", "phone", "tel"},
    "email": {"email", "почта", "e-mail"},
    "address": {"адрес", "address", "адрес регистрации"},
    "status": {"статус", "status"},
    "risk_level": {"риск", "уровень риска", "risk", "risk_level"},
    "tags": {"метки", "теги", "tags"},
    "notes": {"примечания", "заметки", "notes", "комментарий"},
}


def _normalize_header(value: str) -> str:
    return (value or "").strip().lower().replace("ё", "е")


def _map_row(raw: dict) -> dict:
    row = {}
    for key, value in raw.items():
        normalized = _normalize_header(key)
        for field, aliases in HEADER_ALIASES.items():
            if normalized in aliases:
                row[field] = ("" if value is None else str(value)).strip()
                break
    return row


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    value = str(value).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y.%m.%d"):
        try:
            return dt.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_import_file(uploaded_file):
    """Return a list of mapped dict rows from CSV or XLSX."""
    name = (uploaded_file.name or "").lower()
    rows = []
    if name.endswith((".xlsx", ".xlsm")):
        from openpyxl import load_workbook

        wb = load_workbook(uploaded_file, read_only=True, data_only=True)
        ws = wb.active
        iterator = ws.iter_rows(values_only=True)
        headers = [str(h) if h is not None else "" for h in next(iterator)]
        for values in iterator:
            raw = dict(zip(headers, values))
            if any(v not in (None, "") for v in raw.values()):
                rows.append(_map_row(raw))
        wb.close()
        return rows

    raw_bytes = uploaded_file.read()
    text = None
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            text = raw_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError("Не удалось определить кодировку файла. Используйте UTF-8 или CP1251.")

    sample = text[:4096]
    delimiter = ";" if sample.count(";") >= sample.count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    for raw in reader:
        if any((v or "").strip() for v in raw.values()):
            rows.append(_map_row(raw))
    return rows


def import_clients(rows, user, source=None):
    created, errors = 0, []
    for index, row in enumerate(rows, start=2):
        last_name = row.get("last_name", "").strip()
        first_name = row.get("first_name", "").strip()
        if not last_name or not first_name:
            errors.append(f"Строка {index}: не заполнены фамилия и/или имя")
            continue
        gender = row.get("gender", "").strip().lower()
        gender_value = ""
        if gender in {"м", "мж", "мужской", "male", "m"}:
            gender_value = Client.Gender.MALE
        elif gender in {"ж", "женский", "female", "f"}:
            gender_value = Client.Gender.FEMALE

        client = Client.objects.create(
            last_name=last_name,
            first_name=first_name,
            middle_name=row.get("middle_name", ""),
            birth_date=_parse_date(row.get("birth_date")),
            gender=gender_value,
            citizenship=row.get("citizenship") or "РФ",
            inn=row.get("inn", ""),
            snils=row.get("snils", ""),
            phone=row.get("phone", ""),
            email=row.get("email", ""),
            address_registration=row.get("address", ""),
            status=STATUS_MAP.get(row.get("status", "").strip().lower(), Client.Status.ACTIVE),
            risk_level=RISK_MAP.get(row.get("risk_level", "").strip().lower(), Client.Risk.LOW),
            tags=row.get("tags", ""),
            notes=row.get("notes", ""),
            source=source,
            created_by=user,
        )
        if client.phone:
            ClientContact.objects.create(client=client, kind=ClientContact.Kind.PHONE, value=client.phone, is_primary=True)
        if client.email:
            ClientContact.objects.create(client=client, kind=ClientContact.Kind.EMAIL, value=client.email)
        DataEvent.objects.create(
            client=client,
            event_type=DataEvent.Kind.IMPORT,
            title="Запись добавлена импортом",
            description=f"Источник: {source.name if source else 'файл'}",
            source=source,
            created_by=user,
        )
        created += 1
    return created, errors


CSV_HEADERS = [
    "ID", "Фамилия", "Имя", "Отчество", "Дата рождения", "Пол", "Гражданство",
    "ИНН", "СНИЛС", "Телефон", "Email", "Адрес", "Статус", "Риск", "Метки",
    "Источник", "Создан", "Обновлён",
]


def clients_to_csv(queryset):
    buffer = io.StringIO()
    buffer.write("\ufeff")
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(CSV_HEADERS)
    for c in queryset.select_related("source"):
        writer.writerow([
            c.pk, c.last_name, c.first_name, c.middle_name,
            c.birth_date.strftime("%d.%m.%Y") if c.birth_date else "",
            c.get_gender_display(), c.citizenship, c.inn, c.snils, c.phone, c.email,
            c.address_registration, c.get_status_display(), c.get_risk_level_display(), c.tags,
            c.source.name if c.source else "",
            timezone.localtime(c.created_at).strftime("%d.%m.%Y %H:%M"),
            timezone.localtime(c.updated_at).strftime("%d.%m.%Y %H:%M"),
        ])
    return buffer.getvalue()


def client_stats():
    week_ago = timezone.now() - timedelta(days=7)
    qs = Client.objects.filter(is_deleted=False)
    return {
        "total": qs.count(),
        "new_week": qs.filter(created_at__gte=week_ago).count(),
        "checking": qs.filter(status=Client.Status.CHECKING).count(),
        "high_risk": qs.filter(risk_level__in=[Client.Risk.HIGH, Client.Risk.CRITICAL]).count(),
        "by_status": list(qs.values("status").annotate(count=Count("id")).order_by("-count")),
        "by_risk": list(qs.values("risk_level").annotate(count=Count("id")).order_by("-count")),
        "sources": list(
            DataSource.objects.filter(is_active=True)
            .annotate(count=Count("clients", filter=Q(clients__is_deleted=False)))
            .values("id", "name", "kind", "count")
            .order_by("-count")
        ),
    }


def apply_filters(qs, params):
    search = (params.get("search") or "").strip()
    if search:
        qs = qs.filter(
            Q(last_name__icontains=search)
            | Q(first_name__icontains=search)
            | Q(middle_name__icontains=search)
            | Q(inn__icontains=search)
            | Q(snils__icontains=search)
            | Q(phone__icontains=search)
            | Q(email__icontains=search)
        )
    status = params.get("status")
    if status:
        qs = qs.filter(status=status)
    risk = params.get("risk_level")
    if risk:
        qs = qs.filter(risk_level=risk)
    source = params.get("source")
    if source:
        qs = qs.filter(source_id=source)
    tag = (params.get("tag") or "").strip()
    if tag:
        qs = qs.filter(tags__icontains=tag)
    return qs
