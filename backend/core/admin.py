from django.contrib import admin

from .models import (
    AuditLog,
    Client,
    ClientContact,
    ClientData,
    Consent,
    DataEvent,
    DataSource,
    Document,
    Integration,
    Report,
    Role,
    User,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "full_name", "role", "department", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("username", "full_name", "email")


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "birth_date", "status", "risk_level", "source", "updated_at")
    list_filter = ("status", "risk_level", "source", "is_deleted")
    search_fields = ("last_name", "first_name", "middle_name", "inn", "snils", "phone")


admin.site.register([Role, DataSource, ClientContact, ClientData, DataEvent, Document, Consent, AuditLog, Report, Integration])
admin.site.site_header = "ФСБ · Единый реестр"
admin.site.site_title = "ФСБ · Реестр"
