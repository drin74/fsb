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

/
/
/
/
///////
/
"C:\Users\Arman bshsoan\AppData\Local\Python\pythoncore-3.14-64\python.exe" "main.py"
//
/
/
/
/
//Откройте PowerShell/терминал в корне проекта FSB\ и выполните:
docker compose up -d --build
Это поднимет MySQL (3308), Redis (6379) и backend+Django (8010). При старте бэкенда автоматически выполняются миграции и seed_demo.
Проверка: откройте в браузере http://127.0.0.1:8010/
Вход (демо): admin / Admin123! (также operator/Operator123!, analyst/Analyst123!, viewer/Viewer123!).
Остановка: docker compose down (данные БД сохраняются в volume fsb_mysql_data).
Если бэкенд/БД нужны с доступом из сети, убедитесь, что открыт порт 8010/TCP в брандмауэре и в настройках разрешены нужные хосты (в compose сейчас DJANGO_ALLOWED_HOSTS=*).

3) Десктоп-клиент (CustomTkinter)
Нужно: Python 3.11+ (Windows).

Установите зависимости и запустите из папки desktop:
cd FSB\desktop
python -m pip install -r requirements.txt
python main.py
Адрес API берётся из desktop\config.json (api_base). По умолчанию: http://127.0.0.1:8010/api.
Если бэкенд работает на этом же ПК — менять не нужно.
Если бэкенд на другом ПК/сервере — замените на http://<IP_сервера>:8010/api.

\
\
\
Ошибка означает, что MySQL не запущен/недоступен по адресу из backend\.env (обычно 127.0.0.1:3308 при настройке через Docker). Бэкенд сам БД не поднимает — её нужно запустить отдельно.

Что сделать на другом ПК (ваш случай)
Вы уже в backend с активным .venv. Проще всего поднять БД через Docker:

Установите Docker Desktop (если ещё не установлен) и запустите его.
В корне проекта (где лежит docker-compose.yml, у вас это C:\Users\user\Desktop\fsb-main) выполните:
docker compose up -d db
Подождите пару секунд, пока MySQL станет готов (можно проверить: docker compose ps).
Вернитесь в backend и выполните миграции/демо-данные (один раз на чистую БД):
cd C:\Users\user\Desktop\fsb-main\backend
.\.venv\Scripts\activate
python manage.py migrate
python manage.py seed_demo
Запустите сервер:
python manage.py runserver 127.0.0.1:8010
Для доступа с других устройств в сети: python manage.py runserver 0.0.0.0:8010.
После этого откройте http://127.0.0.1:8010/ — логин admin / Admin123!.

