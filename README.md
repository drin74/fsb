# ФСБ — Единый реестр

Кроссплатформенное веб-приложение для единого учёта и обработки данных органов / служб,
соответствующее техническому заданию: **веб (React) + мобильный (Android/Kotlin) + настольный (CustomTkinter)**,
бэкенд на Django + DRF, база данных MySQL.

## Возможности

- Единый реестр записей (`Client`): ФИО, дата рождения, пол, гражданство, ИНН, СНИЛС, паспортные данные,
  телефон, email, адрес регистрации/проживания, статус, уровень риска, метки, примечания, источник.
- CRUD записей через REST API и веб-интерфейс, CSV-импорт / выгрузка, статистика.
- Связанные сущности: контакты, события, дополнительные данные, документы, согласия.
- Журнал аудита действий пользователей.

## Структура

```
FSB/
├── backend/            # Django + Django REST Framework (Python)
│   ├── config/         # settings, urls, wsgi/asgi
│   ├── core/           # модели, API, веб-views, сервисы, миграции
│   ├── templates/      # HTML-шаблоны веб-интерфейса
│   ├── static/         # css/js веб-интерфейса, пример CSV
│   ├── management/commands/seed_demo.py
│   └── docker-compose.yml
├── desktop/            # CustomTkinter (Python) — настольный клиент
├── mobile/             # Android (Kotlin + Jetpack Compose/Retrofit подготовлен?) — Android-клиент
└── docs/               # ТЗ, схемы, архитектура
```

## Технологический стек

| Уровень | Технология |
|---|---|
| Веб-интерфейс | React (TypeScript) |
| Мобильный клиент | Android, Kotlin, Jetpack Compose, Retrofit, OkHttp, Coroutines |
| Десктоп-клиент | Python, CustomTkinter |
| API-шлюз | REST (HTTPS), JWT |
| Backend | Python, Django, Django REST Framework, SimpleJWT |
| База данных | MySQL 8.4 LTS |
| Фоновые задачи | Celery + Redis |
| Хранилище файлов | S3 / MinIO |

## Быстрый старт (локальная разработка)

### 1. База данных (Docker)

```bash
docker compose up -d db
```

### 2. Backend

```bash
cd backend
python -m venv .venv
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8010
```

### 3. Демо-данные

```bash
python manage.py seed_demo
```

### 4. Веб-клиент

Открыть http://127.0.0.1:8010/ — логин `admin / Admin123!`.

### 5. Десктоп-клиент

```bash
pip install -r desktop/requirements.txt
python desktop/main.py
```

### 6. Мобильный клиент

```bash
cd mobile
./gradlew assembleDebug
```

## Демо-учётные записи

| Роль | Логин | Пароль |
|---|---|---|
| Администратор | `admin` | `Admin123!` |
| Оператор | `operator` | `Operator123!` |
| Аналитик | `analyst` | `Analyst123!` |
| Наблюдатель | `viewer` | `Viewer123!` |

## Порты

| Сервис | Порт |
|---|---|
| Django (backend + веб) | `8010` |
| MySQL (docker) | `3308` |


& "C:\Users\Arman bshsoan\AppData\Local\Python\pythoncore-3.14-64\python.exe" "main.py"