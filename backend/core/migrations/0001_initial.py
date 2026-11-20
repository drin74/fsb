

import core.models
import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True, verbose_name='название')),
                ('kind', models.CharField(choices=[('manual', 'Ручной ввод'), ('import', 'Импорт'), ('api', 'Внешний API'), ('crm', 'CRM'), ('other', 'Другое')], default='manual', max_length=20, verbose_name='тип')),
                ('url', models.URLField(blank=True, verbose_name='адрес')),
                ('description', models.TextField(blank=True, verbose_name='описание')),
                ('is_active', models.BooleanField(default=True, verbose_name='активен')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='создан')),
            ],
            options={
                'verbose_name': 'источник данных',
                'verbose_name_plural': 'источники данных',
                'db_table': 'data_sources',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Integration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True, verbose_name='название')),
                ('kind', models.CharField(default='rest', max_length=50, verbose_name='тип')),
                ('base_url', models.URLField(blank=True, verbose_name='адрес')),
                ('api_key', models.CharField(blank=True, max_length=255, verbose_name='API-ключ')),
                ('is_active', models.BooleanField(default=False, verbose_name='активна')),
                ('last_sync_at', models.DateTimeField(blank=True, null=True, verbose_name='последняя синхронизация')),
                ('description', models.TextField(blank=True, verbose_name='описание')),
            ],
            options={
                'verbose_name': 'интеграция',
                'verbose_name_plural': 'интеграции',
                'db_table': 'integrations',
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(max_length=32, unique=True, verbose_name='код')),
                ('name', models.CharField(max_length=100, verbose_name='название')),
                ('description', models.TextField(blank=True, verbose_name='описание')),
            ],
            options={
                'verbose_name': 'роль',
                'verbose_name_plural': 'роли',
                'db_table': 'roles',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('full_name', models.CharField(blank=True, max_length=255, verbose_name='ФИО')),
                ('phone', models.CharField(blank=True, max_length=32, verbose_name='телефон')),
                ('department', models.CharField(blank=True, max_length=150, verbose_name='подразделение')),
                ('position', models.CharField(blank=True, max_length=150, verbose_name='должность')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                ('role', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='core.role', verbose_name='роль')),
            ],
            options={
                'verbose_name': 'сотрудник',
                'verbose_name_plural': 'сотрудники',
                'db_table': 'users',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('create', 'Создание'), ('update', 'Изменение'), ('delete', 'Удаление'), ('view', 'Просмотр'), ('login', 'Вход'), ('logout', 'Выход'), ('import', 'Импорт'), ('export', 'Экспорт')], max_length=20, verbose_name='действие')),
                ('model_name', models.CharField(blank=True, max_length=100, verbose_name='объект')),
                ('object_id', models.CharField(blank=True, max_length=64, verbose_name='ID объекта')),
                ('object_repr', models.CharField(blank=True, max_length=255, verbose_name='описание объекта')),
                ('details', models.JSONField(blank=True, default=dict, verbose_name='детали')),
                ('ip', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='время')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL, verbose_name='сотрудник')),
            ],
            options={
                'verbose_name': 'запись аудита',
                'verbose_name_plural': 'журнал аудита',
                'db_table': 'audit_logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_name', models.CharField(max_length=100, verbose_name='фамилия')),
                ('first_name', models.CharField(max_length=100, verbose_name='имя')),
                ('middle_name', models.CharField(blank=True, max_length=100, verbose_name='отчество')),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name='дата рождения')),
                ('gender', models.CharField(blank=True, choices=[('M', 'Мужской'), ('F', 'Женский')], max_length=1, verbose_name='пол')),
                ('citizenship', models.CharField(blank=True, default='РФ', max_length=100, verbose_name='гражданство')),
                ('inn', models.CharField(blank=True, max_length=12, verbose_name='ИНН')),
                ('snils', models.CharField(blank=True, max_length=14, verbose_name='СНИЛС')),
                ('passport_series', models.CharField(blank=True, max_length=8, verbose_name='серия паспорта')),
                ('passport_number', models.CharField(blank=True, max_length=12, verbose_name='номер паспорта')),
                ('passport_issued_by', models.CharField(blank=True, max_length=255, verbose_name='кем выдан')),
                ('passport_issue_date', models.DateField(blank=True, null=True, verbose_name='дата выдачи')),
                ('address_registration', models.CharField(blank=True, max_length=300, verbose_name='адрес регистрации')),
                ('address_actual', models.CharField(blank=True, max_length=300, verbose_name='адрес проживания')),
                ('phone', models.CharField(blank=True, max_length=32, verbose_name='основной телефон')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email')),
                ('status', models.CharField(choices=[('active', 'Активен'), ('inactive', 'Неактивен'), ('watch', 'Наблюдение'), ('checking', 'На проверке'), ('blocked', 'Заблокирован')], default='active', max_length=20, verbose_name='статус')),
                ('risk_level', models.CharField(choices=[('low', 'Низкий'), ('medium', 'Средний'), ('high', 'Высокий'), ('critical', 'Критический')], default='low', max_length=20, verbose_name='уровень риска')),
                ('tags', models.CharField(blank=True, help_text='Через запятую', max_length=255, verbose_name='метки')),
                ('notes', models.TextField(blank=True, verbose_name='примечания')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='clients/%Y/%m/', verbose_name='фото')),
                ('is_deleted', models.BooleanField(default=False, verbose_name='удалён')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='удалён в')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='создан')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='обновлён')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_clients', to=settings.AUTH_USER_MODEL, verbose_name='создал')),
                ('source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clients', to='core.datasource', verbose_name='источник')),
            ],
            options={
                'verbose_name': 'запись',
                'verbose_name_plural': 'записи',
                'db_table': 'clients',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='ClientContact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('phone', 'Телефон'), ('email', 'Email'), ('telegram', 'Telegram'), ('whatsapp', 'WhatsApp'), ('other', 'Другое')], default='phone', max_length=20, verbose_name='тип')),
                ('value', models.CharField(max_length=255, verbose_name='значение')),
                ('comment', models.CharField(blank=True, max_length=255, verbose_name='комментарий')),
                ('is_primary', models.BooleanField(default=False, verbose_name='основной')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contacts', to='core.client', verbose_name='запись')),
            ],
            options={
                'verbose_name': 'контакт',
                'verbose_name_plural': 'контакты',
                'db_table': 'client_contacts',
                'ordering': ['-is_primary', 'kind'],
            },
        ),
        migrations.CreateModel(
            name='DataEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('update', 'Обновление'), ('check', 'Проверка'), ('incident', 'Инцидент'), ('request', 'Запрос'), ('import', 'Импорт'), ('note', 'Заметка')], default='note', max_length=20, verbose_name='тип')),
                ('title', models.CharField(max_length=200, verbose_name='заголовок')),
                ('description', models.TextField(blank=True, verbose_name='описание')),
                ('occurred_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='произошло')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='core.client', verbose_name='запись')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='events', to=settings.AUTH_USER_MODEL, verbose_name='автор')),
                ('source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='events', to='core.datasource', verbose_name='источник')),
            ],
            options={
                'verbose_name': 'событие',
                'verbose_name_plural': 'события',
                'db_table': 'data_events',
                'ordering': ['-occurred_at'],
            },
        ),
        migrations.CreateModel(
            name='ClientData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('passport', 'Документы'), ('address', 'Адреса'), ('transport', 'Транспорт'), ('job', 'Работа'), ('education', 'Образование'), ('finance', 'Финансы'), ('social', 'Соцсети'), ('other', 'Другое')], default='other', max_length=20, verbose_name='категория')),
                ('key', models.CharField(max_length=150, verbose_name='поле')),
                ('value', models.TextField(verbose_name='значение')),
                ('verified', models.BooleanField(default=False, verbose_name='проверено')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='data_items', to='core.client', verbose_name='запись')),
                ('source', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='data_items', to='core.datasource', verbose_name='источник')),
            ],
            options={
                'verbose_name': 'дополнительные сведения',
                'verbose_name_plural': 'дополнительные сведения',
                'db_table': 'client_data',
                'ordering': ['category', 'key'],
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='название')),
                ('doc_type', models.CharField(blank=True, max_length=100, verbose_name='тип документа')),
                ('file', models.FileField(upload_to=core.models.document_path, verbose_name='файл')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='core.client', verbose_name='запись')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documents', to=settings.AUTH_USER_MODEL, verbose_name='загрузил')),
            ],
            options={
                'verbose_name': 'документ',
                'verbose_name_plural': 'документы',
                'db_table': 'documents',
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='Consent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('consent_type', models.CharField(default='Обработка персональных данных', max_length=150, verbose_name='тип согласия')),
                ('granted', models.BooleanField(default=False, verbose_name='получено')),
                ('valid_until', models.DateField(blank=True, null=True, verbose_name='действует до')),
                ('comment', models.TextField(blank=True, verbose_name='комментарий')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consents', to='core.client', verbose_name='запись')),
                ('document', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='consents', to='core.document', verbose_name='документ')),
            ],
            options={
                'verbose_name': 'согласие',
                'verbose_name_plural': 'согласия',
                'db_table': 'consents',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='название')),
                ('report_type', models.CharField(choices=[('clients', 'Реестр записей'), ('events', 'События'), ('risk', 'Риски'), ('audit', 'Аудит')], default='clients', max_length=20, verbose_name='тип')),
                ('params', models.JSONField(blank=True, default=dict, verbose_name='параметры')),
                ('status', models.CharField(default='готов', max_length=20, verbose_name='статус')),
                ('file', models.FileField(blank=True, null=True, upload_to='reports/%Y/%m/', verbose_name='файл')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='создан')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reports', to=settings.AUTH_USER_MODEL, verbose_name='создал')),
            ],
            options={
                'verbose_name': 'отчёт',
                'verbose_name_plural': 'отчёты',
                'db_table': 'reports',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['last_name', 'first_name'], name='clients_last_na_7dc725_idx'),
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['status'], name='clients_status_98ee60_idx'),
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['risk_level'], name='clients_risk_le_e45799_idx'),
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['is_deleted'], name='clients_is_dele_edc29c_idx'),
        ),
    ]
