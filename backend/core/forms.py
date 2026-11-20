from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Client, ClientContact, ClientData, Consent, DataEvent, DataSource, Document, Role, User

INPUT = "input"
SELECT = "input select"
TEXTAREA = "input textarea"
CHECK = "checkbox"


class StyledFormMixin:
    def style(self):
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", CHECK)
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", SELECT)
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("class", TEXTAREA)
                widget.attrs.setdefault("rows", 3)
            else:
                widget.attrs.setdefault("class", INPUT)
        return self


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Логин",
        widget=forms.TextInput(attrs={"class": INPUT, "placeholder": "admin", "autofocus": True}),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"class": INPUT, "placeholder": "••••••••"}),
    )


class ClientForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            "last_name", "first_name", "middle_name", "birth_date", "gender", "citizenship",
            "inn", "snils", "passport_series", "passport_number", "passport_issued_by",
            "passport_issue_date", "address_registration", "address_actual", "phone", "email",
            "status", "risk_level", "tags", "source", "photo", "notes",
        ]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "passport_issue_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "notes": forms.Textarea(attrs={"rows": 4}),
            "tags": forms.TextInput(attrs={"placeholder": "Например: транспорт, наблюдение"}),
            "passport_series": forms.TextInput(attrs={"placeholder": "0000"}),
            "passport_number": forms.TextInput(attrs={"placeholder": "000000"}),
            "phone": forms.TextInput(attrs={"placeholder": "+7 900 000-00-00"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["birth_date"].input_formats = ["%Y-%m-%d", "%d.%m.%Y"]
        self.fields["passport_issue_date"].input_formats = ["%Y-%m-%d", "%d.%m.%Y"]
        self.style()


class ContactForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ClientContact
        fields = ["kind", "value", "comment", "is_primary"]
        widgets = {"value": forms.TextInput(attrs={"placeholder": "+7 ..."})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style()


class ClientDataForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ClientData
        fields = ["category", "key", "value", "source", "verified"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style()


class EventForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = DataEvent
        fields = ["event_type", "title", "description", "source", "occurred_at"]
        widgets = {"occurred_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["occurred_at"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S"]
        self.style()


class DocumentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Document
        fields = ["title", "doc_type", "file"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style()


class ConsentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Consent
        fields = ["consent_type", "granted", "valid_until", "comment"]
        widgets = {"valid_until": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["valid_until"].input_formats = ["%Y-%m-%d", "%d.%m.%Y"]
        self.style()


class DataSourceForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = DataSource
        fields = ["name", "kind", "url", "description", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style()


class UserForm(StyledFormMixin, forms.ModelForm):
    password = forms.CharField(
        label="Пароль", required=False, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"})
    )
    password2 = forms.CharField(label="Повтор пароля", required=False, widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ["username", "full_name", "email", "phone", "department", "position", "role", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = Role.objects.all()
        if self.instance.pk:
            self.fields["password"].help_text = "Оставьте пустым, чтобы не менять"
        self.style()

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password"), cleaned.get("password2")
        if p1 != p2:
            self.add_error("password2", "Пароли не совпадают")
        if not self.instance.pk and not p1:
            self.add_error("password", "Пароль обязателен для нового сотрудника")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user


class ImportForm(StyledFormMixin, forms.Form):
    file = forms.FileField(label="Файл CSV / XLSX")
    source = forms.ModelChoiceField(label="Источник данных", queryset=DataSource.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style()
