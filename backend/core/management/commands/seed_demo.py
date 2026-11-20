import datetime as dt
import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    AuditLog,
    Client,
    ClientContact,
    ClientData,
    Consent,
    DataEvent,
    DataSource,
    Report,
    Role,
    User,
)

ROLES = [
    ("admin", "Администратор", "Полный доступ, управление сотрудниками и интеграциями"),
    ("operator", "Оператор", "Создание и изменение записей, импорт и экспорт"),
    ("analyst", "Аналитик", "Просмотр реестра, событий и отчётов"),
    ("viewer", "Наблюдатель", "Только просмотр данных"),
]

USERS = [
    ("admin", "Администратор системы", "admin", "Администрация", "Начальник отдела", "Admin123!"),
    ("operator", "Смирнов Алексей Петрович", "operator", "Оперативный отдел", "Старший оператор", "Operator123!"),
    ("analyst", "Волкова Ирина Андреевна", "analyst", "Аналитический отдел", "Аналитик", "Analyst123!"),
    ("viewer", "Морозов Павел Сергеевич", "viewer", "Дежурная смена", "Дежурный", "Viewer123!"),
]

SOURCES = [
    ("Ручной ввод", DataSource.Kind.MANUAL, "Карточка создана сотрудником вручную"),
    ("Импорт CSV", DataSource.Kind.IMPORT, "Массовая загрузка из файла"),
    ("Единый портал услуг", DataSource.Kind.API, "https://example.gov/api", "Интеграция по REST API"),
    ("CRM «Орбита»", DataSource.Kind.CRM, "https://crm.example.ru", "Внутренняя CRM-система"),
    ("Банк данных партнёра", DataSource.Kind.API, "https://partner.example.ru", "Партнёрский источник"),
]

CLIENTS = [
    ("Иванов", "Иван", "Иванович", "1987-04-12", "M", "770123456789", "123-456-789 01", "+7 900 123-45-67", "ivanov@example.ru", "г. Москва, ул. Тверская, д. 10", "active", "low", "транспорт", "Москва"),
    ("Петрова", "Анна", "Сергеевна", "1992-09-03", "F", "780987654321", "987-654-321 02", "+7 921 555-11-22", "petrova@example.ru", "г. Санкт-Петербург, Невский пр., д. 25", "watch", "medium", "финансы", "Санкт-Петербург"),
    ("Сидоров", "Максим", "Олегович", "1985-01-27", "M", "500111223344", "111-222-333 04", "+7 916 222-33-44", "sidorov@example.ru", "Московская обл., г. Химки, ул. Мира, д. 4", "checking", "high", "транспорт, наблюдение", "Химки"),
    ("Кузнецова", "Мария", "Андреевна", "1998-06-15", "F", "770333445566", "333-444-555 06", "+7 903 777-88-99", "kuznetsova@example.ru", "г. Казань, ул. Баумана, д. 12", "active", "low", "образование", "Казань"),
    ("Соколов", "Денис", "Владимирович", "1979-11-08", "M", "660555667788", "555-666-777 08", "+7 912 444-55-66", "sokolov@example.ru", "г. Екатеринбург, ул. Ленина, д. 33", "blocked", "critical", "инцидент", "Екатеринбург"),
    ("Морозова", "Елена", "Викторовна", "1990-03-21", "F", "770654321098", "654-321-098 12", "+7 905 111-22-33", "morozova@example.ru", "г. Новосибирск, ул. Красный пр., д. 18", "active", "low", "соцсети", "Новосибирск"),
    ("Волков", "Андрей", "Николаевич", "1983-07-30", "M", "500777889900", "777-888-990 14", "+7 911 333-44-55", "volkov@example.ru", "Ленинградская обл., г. Гатчина, ул. Соборная, д. 7", "watch", "medium", "финансы, транспорт", "Гатчина"),
    ("Лебедева", "Ольга", "Дмитриевна", "1995-12-05", "F", "770888990011", "888-990-011 16", "+7 926 555-66-77", "lebedeva@example.ru", "г. Москва, ул. Арбат, д. 31", "active", "low", "образование", "Москва"),
    ("Новиков", "Сергей", "Александрович", "1976-02-14", "M", "660111223355", "111-223-355 18", "+7 913 777-88-99", "novikov@example.ru", "г. Красноярск, ул. Мира, д. 55", "checking", "high", "инцидент, наблюдение", "Красноярск"),
    ("Фёдорова", "Татьяна", "Игоревна", "1988-08-19", "F", "770222334466", "222-334-466 20", "+7 903 999-00-11", "fedorova@example.ru", "г. Нижний Новгород, ул. Большая Покровская, д. 9", "active", "low", "работа", "Нижний Новгород"),
    ("Максимов", "Павел", "Юрьевич", "1993-10-11", "M", "780333445577", "333-445-577 22", "+7 921 123-45-67", "maksimov@example.ru", "г. Санкт-Петербург, ул. Литейный пр., д. 44", "watch", "medium", "транспорт", "Санкт-Петербург"),
    ("Захарова", "Ксения", "Олеговна", "1999-04-28", "F", "770444556688", "444-556-688 24", "+7 915 234-56-78", "zaharova@example.ru", "г. Москва, ул. Профсоюзная, д. 61", "active", "low", "соцсети", "Москва"),
    ("Борисов", "Артём", "Валерьевич", "1981-06-07", "M", "500555667799", "555-667-799 26", "+7 917 345-67-89", "borisov@example.ru", "г. Самара, ул. Куйбышева, д. 15", "blocked", "high", "инцидент", "Самара"),
    ("Григорьева", "Наталья", "Петровна", "1974-01-16", "F", "660666778800", "666-778-800 28", "+7 908 456-78-90", "grigorieva@example.ru", "г. Омск, ул. Ленина, д. 3", "inactive", "low", "работа", "Омск"),
    ("Егоров", "Дмитрий", "Сергеевич", "1986-05-23", "M", "770777889911", "777-889-911 30", "+7 909 567-89-01", "egorov@example.ru", "г. Москва, ул. Сокольнический вал, д. 8", "active", "medium", "финансы", "Москва"),
    ("Панова", "Виктория", "Алексеевна", "1997-09-09", "F", "780888990022", "888-990-022 32", "+7 931 678-90-12", "panova@example.ru", "г. Санкт-Петербург, ул. Садовая, д. 21", "active", "low", "образование", "Санкт-Петербург"),
    ("Тарасов", "Илья", "Максимович", "1989-03-02", "M", "770999001133", "999-001-133 34", "+7 985 789-01-23", "tarasov@example.ru", "г. Москва, ул. Ленинский пр., д. 72", "checking", "critical", "наблюдение, инцидент", "Москва"),
    ("Ковалёва", "Алина", "Романовна", "2000-11-27", "F", "501000112244", "000-112-244 36", "+7 919 890-12-34", "kovaleva@example.ru", "г. Ростов-на-Дону, ул. Пушкинская, д. 14", "active", "low", "соцсети", "Ростов-на-Дону"),
    ("Фролов", "Никита", "Денисович", "1984-07-04", "M", "661111223355", "111-223-355 38", "+7 950 901-23-45", "frolov@example.ru", "г. Пермь, ул. Комсомольский пр., д. 27", "watch", "medium", "транспорт, работа", "Пермь"),
    ("Смирнова", "Дарья", "Константиновна", "1994-02-18", "F", "770121314151", "121-314-151 40", "+7 965 012-34-56", "smirnova@example.ru", "г. Москва, ул. Щёлковское ш., д. 90", "active", "low", "медицина", "Москва"),
    ("Козлов", "Роман", "Евгеньевич", "1978-12-12", "M", "500232425262", "232-425-262 42", "+7 999 123-00-45", "kozlov@example.ru", "г. Воронеж, ул. Кольцовская, д. 6", "inactive", "medium", "финансы", "Воронеж"),
    ("Орлова", "Полина", "Максимовна", "1996-06-30", "F", "780343536373", "343-536-373 44", "+7 977 234-11-56", "orlova@example.ru", "г. Санкт-Петербург, ул. Московский пр., д. 101", "active", "low", "образование", "Санкт-Петербург"),
    ("Дмитриев", "Алексей", "Ильич", "1982-08-25", "M", "770454647484", "454-647-484 46", "+7 962 345-22-67", "dmitriev@example.ru", "г. Москва, ул. Кутузовский пр., д. 19", "checking", "high", "транспорт, наблюдение", "Москва"),
    ("Алексеева", "Софья", "Владиславовна", "2001-01-05", "F", "500565758595", "565-758-595 48", "+7 988 456-33-78", "alekseeva@example.ru", "г. Краснодар, ул. Красная, д. 40", "active", "low", "соцсети", "Краснодар"),
    ("Гусев", "Егор", "Андреевич", "1991-10-17", "M", "770676869707", "676-869-707 50", "+7 903 567-44-89", "gusev@example.ru", "г. Москва, ул. Варшавское ш., д. 12", "watch", "medium", "работа, финансы", "Москва"),
    ("Белова", "Екатерина", "Николаевна", "1987-05-08", "F", "780787879808", "787-879-808 52", "+7 921 678-55-90", "belova@example.ru", "г. Санкт-Петербург, ул. Загородный пр., д. 33", "active", "low", "медицина", "Санкт-Петербург"),
]

DATA_ITEMS = [
    ("transport", "Автомобиль", "Lada Vesta, гос. номер А123ВС77"),
    ("job", "Место работы", "ООО «Северная логистика», менеджер"),
    ("finance", "Банковский счёт", "Счёт в ПАО «Банк» (реквизиты скрыты)"),
    ("social", "Профиль в соцсети", "https://example.social/profile"),
    ("education", "Образование", "Высшее, экономический факультет"),
]

EVENTS = [
    ("update", "Проверка анкетных данных", "Сверка с источником завершена, расхождений не выявлено."),
    ("check", "Плановая проверка", "Запись включена в ежеквартальную проверку."),
    ("note", "Комментарий оператора", "Требуется уточнение адреса регистрации."),
    ("incident", "Инцидент безопасности", "Зафиксирована попытка доступа с нетипичного устройства."),
    ("request", "Запрос в ведомство", "Направлен официальный запрос на подтверждение сведений."),
    ("import", "Импорт из внешнего источника", "Сведения обновлены по данным партнёрского API."),
]


class Command(BaseCommand):
    help = "Создаёт роли, сотрудников, источники и демонстрационный реестр."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Удалить существующие записи перед заполнением")

    def handle(self, *args, **options):
        random.seed(42)
        if options["reset"]:
            Client.objects.all().delete()
            AuditLog.objects.all().delete()
            Report.objects.all().delete()
            self.stdout.write(self.style.WARNING("Демонстрационные записи удалены."))

        roles = {}
        for code, name, description in ROLES:
            role, _ = Role.objects.update_or_create(code=code, defaults={"name": name, "description": description})
            roles[code] = role

        for username, full_name, role_code, department, position, password in USERS:
            user, created = User.objects.get_or_create(username=username)
            user.full_name = full_name
            user.role = roles[role_code]
            user.department = department
            user.position = position
            user.email = f"{username}@fsb.local"
            user.is_staff = True
            user.is_superuser = role_code == "admin"
            if created or options["reset"]:
                user.set_password(password)
            user.save()
            if created:
                self.stdout.write(f"  · сотрудник {username} создан")

        sources = {}
        for name, kind, *rest in SOURCES:
            url = rest[0] if rest and rest[0].startswith("http") else ""
            description = rest[-1]
            source, _ = DataSource.objects.update_or_create(
                name=name, defaults={"kind": kind, "url": url, "description": description, "is_active": True}
            )
            sources[name] = source

        if Client.objects.exists() and not options["reset"]:
            self.stdout.write(self.style.WARNING("Записи уже существуют. Используйте --reset для перезаполнения."))
            return

        admin = User.objects.get(username="admin")
        operator = User.objects.get(username="operator")
        source_list = list(sources.values())
        now = timezone.now()
        created = 0

        for index, row in enumerate(CLIENTS):
            (
                last_name, first_name, middle_name, birth, gender, inn, snils,
                phone, email, address, status, risk, tags, city,
            ) = row
            client = Client.objects.create(
                last_name=last_name,
                first_name=first_name,
                middle_name=middle_name,
                birth_date=dt.date.fromisoformat(birth),
                gender=gender,
                citizenship="РФ",
                inn=inn,
                snils=snils,
                passport_series=f"{4500 + index:04d}",
                passport_number=f"{100000 + index * 137:06d}",
                passport_issued_by=f"ОВД района «{city}»",
                passport_issue_date=dt.date(2010 + index % 8, (index % 12) + 1, 12),
                address_registration=address,
                address_actual=address if index % 4 else f"г. Москва, ул. Складская, д. {index + 1}",
                phone=phone,
                email=email,
                status=status,
                risk_level=risk,
                tags=tags,
                notes="Демонстрационная запись. Персональные данные вымышлены.",
                source=source_list[index % len(source_list)],
                created_by=admin if index % 2 == 0 else operator,
                created_at=now - dt.timedelta(days=index * 3 + 1),
                updated_at=now - dt.timedelta(days=index % 9, hours=index),
            )
            ClientContact.objects.create(client=client, kind=ClientContact.Kind.PHONE, value=phone, is_primary=True)
            ClientContact.objects.create(client=client, kind=ClientContact.Kind.EMAIL, value=email)
            if index % 7 == 0:
                ClientContact.objects.create(
                    client=client, kind=ClientContact.Kind.TELEGRAM, value=f"@demo_{index}", comment="Резервный канал"
                )

            category, key, value = DATA_ITEMS[index % len(DATA_ITEMS)]
            ClientData.objects.create(client=client, category=category, key=key, value=value, source=client.source, verified=index % 3 == 0)

            for event_offset in range(2 + index % 3):
                event_type, title, description = EVENTS[(index + event_offset) % len(EVENTS)]
                DataEvent.objects.create(
                    client=client,
                    event_type=event_type,
                    title=title,
                    description=description,
                    source=client.source,
                    created_by=operator if event_offset % 2 else admin,
                    occurred_at=now - dt.timedelta(days=index * 2 + event_offset, hours=event_offset * 5),
                )

            if index % 5 != 4:
                Consent.objects.create(
                    client=client,
                    consent_type="Обработка персональных данных",
                    granted=True,
                    valid_until=dt.date.today() + dt.timedelta(days=365),
                    comment="Согласие получено в электронной форме",
                )
            created += 1

        AuditLog.objects.create(
            user=admin,
            action=AuditLog.Action.IMPORT,
            model_name="Client",
            object_repr="Демонстрационный реестр",
            details={"created": created},
            ip="127.0.0.1",
        )
        Report.objects.create(
            name="Демонстрационный реестр",
            report_type=Report.Kind.CLIENTS,
            params={"source": "seed"},
            created_by=admin,
        )

        self.stdout.write(self.style.SUCCESS(f"Готово: {created} записей, {len(USERS)} сотрудников, {len(SOURCES)} источников."))
        self.stdout.write("Вход: admin / Admin123!  ·  operator / Operator123!  ·  analyst / Analyst123!")
