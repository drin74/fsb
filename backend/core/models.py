from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Role(models.Model):
    code = models.SlugField("код", max_length=32, unique=True)
    name = models.CharField("название", max_length=100)
    description = models.TextField("описание", blank=True)

    class Meta:
        db_table = "roles"
        verbose_name = "роль"
        verbose_name_plural = "роли"
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    full_name = models.CharField("ФИО", max_length=255, blank=True)
    role = models.ForeignKey(
        Role, verbose_name="роль", null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
    )
    phone = models.CharField("телефон", max_length=32, blank=True)
    department = models.CharField("подразделение", max_length=150, blank=True)
    position = models.CharField("должность", max_length=150, blank=True)

    class Meta:
        db_table = "users"
        verbose_name = "сотрудник"
        verbose_name_plural = "сотрудники"

    @property
    def display_name(self) -> str:
        return self.full_name or self.get_full_name() or self.username

    @property
    def role_code(self) -> str:
        if self.is_superuser:
            return "admin"
        return self.role.code if self.role else "viewer"

    @property
    def can_edit(self) -> bool:
        return self.is_superuser or self.role_code in {"admin", "operator"}

    def __str__(self):
        return self.display_name


class DataSource(models.Model):
    class Kind(models.TextChoices):
        MANUAL = "manual", "Ручной ввод"
        IMPORT = "import", "Импорт"
        API = "api", "Внешний API"
        CRM = "crm", "CRM"
        OTHER = "other", "Другое"

    name = models.CharField("название", max_length=150, unique=True)
    kind = models.CharField("тип", max_length=20, choices=Kind.choices, default=Kind.MANUAL)
    url = models.URLField("адрес", blank=True)
    description = models.TextField("описание", blank=True)
    is_active = models.BooleanField("активен", default=True)
    created_at = models.DateTimeField("создан", auto_now_add=True)

    class Meta:
        db_table = "data_sources"
        verbose_name = "источник данных"
        verbose_name_plural = "источники данных"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Client(models.Model):
    class Gender(models.TextChoices):
        MALE = "M", "Мужской"
        FEMALE = "F", "Женский"

    class Status(models.TextChoices):
        ACTIVE = "active", "Активен"
        INACTIVE = "inactive", "Неактивен"
        WATCH = "watch", "Наблюдение"
        CHECKING = "checking", "На проверке"
        BLOCKED = "blocked", "Заблокирован"

    class Risk(models.TextChoices):
        LOW = "low", "Низкий"
        MEDIUM = "medium", "Средний"
        HIGH = "high", "Высокий"
        CRITICAL = "critical", "Критический"

    last_name = models.CharField("фамилия", max_length=100)
    first_name = models.CharField("имя", max_length=100)
    middle_name = models.CharField("отчество", max_length=100, blank=True)
    birth_date = models.DateField("дата рождения", null=True, blank=True)
    gender = models.CharField("пол", max_length=1, choices=Gender.choices, blank=True)
    citizenship = models.CharField("гражданство", max_length=100, blank=True, default="РФ")

    inn = models.CharField("ИНН", max_length=12, blank=True)
    snils = models.CharField("СНИЛС", max_length=14, blank=True)
    passport_series = models.CharField("серия паспорта", max_length=8, blank=True)
    passport_number = models.CharField("номер паспорта", max_length=12, blank=True)
    passport_issued_by = models.CharField("кем выдан", max_length=255, blank=True)
    passport_issue_date = models.DateField("дата выдачи", null=True, blank=True)

    address_registration = models.CharField("адрес регистрации", max_length=300, blank=True)
    address_actual = models.CharField("адрес проживания", max_length=300, blank=True)
    phone = models.CharField("основной телефон", max_length=32, blank=True)
    email = models.EmailField("email", blank=True)

    status = models.CharField("статус", max_length=20, choices=Status.choices, default=Status.ACTIVE)
    risk_level = models.CharField("уровень риска", max_length=20, choices=Risk.choices, default=Risk.LOW)
    tags = models.CharField("метки", max_length=255, blank=True, help_text="Через запятую")
    notes = models.TextField("примечания", blank=True)
    photo = models.ImageField("фото", upload_to="clients/%Y/%m/", null=True, blank=True)
    source = models.ForeignKey(
        DataSource, verbose_name="источник", null=True, blank=True, on_delete=models.SET_NULL, related_name="clients"
    )

    is_deleted = models.BooleanField("удалён", default=False)
    deleted_at = models.DateTimeField("удалён в", null=True, blank=True)
    created_by = models.ForeignKey(
        User, verbose_name="создал", null=True, blank=True, on_delete=models.SET_NULL, related_name="created_clients"
    )
    created_at = models.DateTimeField("создан", auto_now_add=True)
    updated_at = models.DateTimeField("обновлён", auto_now=True)

    class Meta:
        db_table = "clients"
        verbose_name = "запись"
        verbose_name_plural = "записи"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["status"]),
            models.Index(fields=["risk_level"]),
            models.Index(fields=["is_deleted"]),
        ]

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(p for p in parts if p).strip()

    @property
    def short_name(self) -> str:
        initials = "".join(part[0] + "." for part in [self.first_name, self.middle_name] if part)
        return f"{self.last_name} {initials}".strip()

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = timezone.localdate()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def __str__(self):
        return self.full_name


class ClientContact(models.Model):
    class Kind(models.TextChoices):
        PHONE = "phone", "Телефон"
        EMAIL = "email", "Email"
        TELEGRAM = "telegram", "Telegram"
        WHATSAPP = "whatsapp", "WhatsApp"
        OTHER = "other", "Другое"

    client = models.ForeignKey(Client, verbose_name="запись", on_delete=models.CASCADE, related_name="contacts")
    kind = models.CharField("тип", max_length=20, choices=Kind.choices, default=Kind.PHONE)
    value = models.CharField("значение", max_length=255)
    comment = models.CharField("комментарий", max_length=255, blank=True)
    is_primary = models.BooleanField("основной", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "client_contacts"
        verbose_name = "контакт"
        verbose_name_plural = "контакты"
        ordering = ["-is_primary", "kind"]

    def __str__(self):
        return f"{self.get_kind_display()}: {self.value}"


class ClientData(models.Model):
    class Category(models.TextChoices):
        PASSPORT = "passport", "Документы"
        ADDRESS = "address", "Адреса"
        TRANSPORT = "transport", "Транспорт"
        JOB = "job", "Работа"
        EDUCATION = "education", "Образование"
        FINANCE = "finance", "Финансы"
        SOCIAL = "social", "Соцсети"
        OTHER = "other", "Другое"

    client = models.ForeignKey(Client, verbose_name="запись", on_delete=models.CASCADE, related_name="data_items")
    category = models.CharField("категория", max_length=20, choices=Category.choices, default=Category.OTHER)
    key = models.CharField("поле", max_length=150)
    value = models.TextField("значение")
    source = models.ForeignKey(
        DataSource, verbose_name="источник", null=True, blank=True, on_delete=models.SET_NULL, related_name="data_items"
    )
    verified = models.BooleanField("проверено", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "client_data"
        verbose_name = "дополнительные сведения"
        verbose_name_plural = "дополнительные сведения"
        ordering = ["category", "key"]

    def __str__(self):
        return f"{self.key}: {self.value[:40]}"


class DataEvent(models.Model):
    class Kind(models.TextChoices):
        UPDATE = "update", "Обновление"
        CHECK = "check", "Проверка"
        INCIDENT = "incident", "Инцидент"
        REQUEST = "request", "Запрос"
        IMPORT = "import", "Импорт"
        NOTE = "note", "Заметка"

    client = models.ForeignKey(Client, verbose_name="запись", on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField("тип", max_length=20, choices=Kind.choices, default=Kind.NOTE)
    title = models.CharField("заголовок", max_length=200)
    description = models.TextField("описание", blank=True)
    source = models.ForeignKey(
        DataSource, verbose_name="источник", null=True, blank=True, on_delete=models.SET_NULL, related_name="events"
    )
    occurred_at = models.DateTimeField("произошло", default=timezone.now)
    created_by = models.ForeignKey(
        User, verbose_name="автор", null=True, blank=True, on_delete=models.SET_NULL, related_name="events"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "data_events"
        verbose_name = "событие"
        verbose_name_plural = "события"
        ordering = ["-occurred_at"]

    def __str__(self):
        return self.title


def document_path(instance, filename):
    return f"documents/{timezone.now():%Y/%m}/{filename}"


class Document(models.Model):
    client = models.ForeignKey(Client, verbose_name="запись", on_delete=models.CASCADE, related_name="documents")
    title = models.CharField("название", max_length=200)
    doc_type = models.CharField("тип документа", max_length=100, blank=True)
    file = models.FileField("файл", upload_to=document_path)
    uploaded_by = models.ForeignKey(
        User, verbose_name="загрузил", null=True, blank=True, on_delete=models.SET_NULL, related_name="documents"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "documents"
        verbose_name = "документ"
        verbose_name_plural = "документы"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title


class Consent(models.Model):
    client = models.ForeignKey(Client, verbose_name="запись", on_delete=models.CASCADE, related_name="consents")
    consent_type = models.CharField("тип согласия", max_length=150, default="Обработка персональных данных")
    granted = models.BooleanField("получено", default=False)
    valid_until = models.DateField("действует до", null=True, blank=True)
    comment = models.TextField("комментарий", blank=True)
    document = models.ForeignKey(
        Document, verbose_name="документ", null=True, blank=True, on_delete=models.SET_NULL, related_name="consents"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "consents"
        verbose_name = "согласие"
        verbose_name_plural = "согласия"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.consent_type}: {'да' if self.granted else 'нет'}"


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Создание"
        UPDATE = "update", "Изменение"
        DELETE = "delete", "Удаление"
        VIEW = "view", "Просмотр"
        LOGIN = "login", "Вход"
        LOGOUT = "logout", "Выход"
        IMPORT = "import", "Импорт"
        EXPORT = "export", "Экспорт"

    user = models.ForeignKey(
        User, verbose_name="сотрудник", null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs"
    )
    action = models.CharField("действие", max_length=20, choices=Action.choices)
    model_name = models.CharField("объект", max_length=100, blank=True)
    object_id = models.CharField("ID объекта", max_length=64, blank=True)
    object_repr = models.CharField("описание объекта", max_length=255, blank=True)
    details = models.JSONField("детали", default=dict, blank=True)
    ip = models.GenericIPAddressField("IP", null=True, blank=True)
    created_at = models.DateTimeField("время", auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        verbose_name = "запись аудита"
        verbose_name_plural = "журнал аудита"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_action_display()} · {self.object_repr}"


class Report(models.Model):
    class Kind(models.TextChoices):
        CLIENTS = "clients", "Реестр записей"
        EVENTS = "events", "События"
        RISK = "risk", "Риски"
        AUDIT = "audit", "Аудит"

    name = models.CharField("название", max_length=200)
    report_type = models.CharField("тип", max_length=20, choices=Kind.choices, default=Kind.CLIENTS)
    params = models.JSONField("параметры", default=dict, blank=True)
    status = models.CharField("статус", max_length=20, default="готов")
    file = models.FileField("файл", upload_to="reports/%Y/%m/", null=True, blank=True)
    created_by = models.ForeignKey(
        User, verbose_name="создал", null=True, blank=True, on_delete=models.SET_NULL, related_name="reports"
    )
    created_at = models.DateTimeField("создан", auto_now_add=True)

    class Meta:
        db_table = "reports"
        verbose_name = "отчёт"
        verbose_name_plural = "отчёты"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Integration(models.Model):
    name = models.CharField("название", max_length=150, unique=True)
    kind = models.CharField("тип", max_length=50, default="rest")
    base_url = models.URLField("адрес", blank=True)
    api_key = models.CharField("API-ключ", max_length=255, blank=True)
    is_active = models.BooleanField("активна", default=False)
    last_sync_at = models.DateTimeField("последняя синхронизация", null=True, blank=True)
    description = models.TextField("описание", blank=True)

    class Meta:
        db_table = "integrations"
        verbose_name = "интеграция"
        verbose_name_plural = "интеграции"

    def __str__(self):
        return self.name
