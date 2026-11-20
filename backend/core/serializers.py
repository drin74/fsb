from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

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


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "code", "name", "description"]


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    role_name = serializers.CharField(source="role.name", read_only=True)
    role_code = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "password", "full_name", "display_name", "email", "phone",
            "department", "position", "role", "role_name", "role_code", "is_active",
            "is_superuser", "date_joined", "last_login",
        ]
        read_only_fields = ["date_joined", "last_login", "is_superuser"]

    def validate_password(self, value):
        if value:
            validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", "") or User.objects.make_random_password()
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", "")
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
        return user


class FSBTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class DataSourceSerializer(serializers.ModelSerializer):
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    clients_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DataSource
        fields = ["id", "name", "kind", "kind_display", "url", "description", "is_active", "clients_count", "created_at"]


class ClientContactSerializer(serializers.ModelSerializer):
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = ClientContact
        fields = ["id", "client", "kind", "kind_display", "value", "comment", "is_primary", "created_at"]


class ClientDataSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    source_name = serializers.CharField(source="source.name", read_only=True)

    class Meta:
        model = ClientData
        fields = [
            "id", "client", "category", "category_display", "key", "value",
            "source", "source_name", "verified", "created_at",
        ]


class DataEventSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source="get_event_type_display", read_only=True)
    source_name = serializers.CharField(source="source.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.display_name", read_only=True)

    class Meta:
        model = DataEvent
        fields = [
            "id", "client", "event_type", "event_type_display", "title", "description",
            "source", "source_name", "occurred_at", "created_by", "created_by_name", "created_at",
        ]
        read_only_fields = ["created_by"]


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source="uploaded_by.display_name", read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ["id", "client", "title", "doc_type", "file", "file_url", "uploaded_by", "uploaded_by_name", "uploaded_at"]
        read_only_fields = ["uploaded_by"]

    def get_file_url(self, obj):
        if not obj.file:
            return None
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url


class ConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consent
        fields = ["id", "client", "consent_type", "granted", "valid_until", "comment", "document", "created_at"]


class ClientListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    risk_display = serializers.CharField(source="get_risk_level_display", read_only=True)
    source_name = serializers.CharField(source="source.name", read_only=True)
    primary_phone = serializers.SerializerMethodField()
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = Client
        fields = [
            "id", "last_name", "first_name", "middle_name", "full_name", "birth_date", "age",
            "gender", "citizenship", "phone", "email", "inn", "snils", "status",
            "status_display", "risk_level", "risk_display", "tags", "source", "source_name",
            "primary_phone", "created_at", "updated_at", "photo",
        ]

    def get_primary_phone(self, obj):
        contact = next((c for c in obj.contacts.all() if c.is_primary), None)
        return contact.value if contact else obj.phone


class NullableDateField(serializers.DateField):
    def to_internal_value(self, value):
        if value is None or value == "":
            return None
        return super().to_internal_value(value)


class ClientSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    short_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    tag_list = serializers.ListField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    risk_display = serializers.CharField(source="get_risk_level_display", read_only=True)
    gender_display = serializers.CharField(source="get_gender_display", read_only=True)
    source_name = serializers.CharField(source="source.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.display_name", read_only=True)
    contacts = ClientContactSerializer(many=True, read_only=True)
    data_items = ClientDataSerializer(many=True, read_only=True)
    events = DataEventSerializer(many=True, read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    consents = ConsentSerializer(many=True, read_only=True)
    birth_date = NullableDateField(required=False, allow_null=True)
    passport_issue_date = NullableDateField(required=False, allow_null=True)

    class Meta:
        model = Client
        fields = [
            "id", "last_name", "first_name", "middle_name", "full_name", "short_name",
            "birth_date", "age", "gender", "gender_display", "citizenship", "inn", "snils",
            "passport_series", "passport_number", "passport_issued_by", "passport_issue_date",
            "address_registration", "address_actual", "phone", "email", "status", "status_display",
            "risk_level", "risk_display", "tags", "tag_list", "notes", "photo", "source",
            "source_name", "is_deleted", "created_by", "created_by_name", "created_at", "updated_at",
            "contacts", "data_items", "events", "documents", "consents",
        ]
        read_only_fields = ["is_deleted", "created_by", "created_at", "updated_at"]


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.display_name", read_only=True)
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id", "user", "user_name", "action", "action_display", "model_name",
            "object_id", "object_repr", "details", "ip", "created_at",
        ]


class ReportSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.display_name", read_only=True)
    report_type_display = serializers.CharField(source="get_report_type_display", read_only=True)

    class Meta:
        model = Report
        fields = [
            "id", "name", "report_type", "report_type_display", "params", "status",
            "file", "created_by", "created_by_name", "created_at",
        ]
        read_only_fields = ["created_by", "created_at"]


class IntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integration
        fields = "__all__"
