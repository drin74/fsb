from functools import wraps
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import services
from .forms import (
    ClientDataForm,
    ClientForm,
    ConsentForm,
    ContactForm,
    DataSourceForm,
    DocumentForm,
    EventForm,
    ImportForm,
    LoginForm,
    UserForm,
)
from .models import AuditLog, Client, ClientData, ClientContact, Consent, DataEvent, DataSource, Document, User


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.role_code == "admin"):
            messages.error(request, "Раздел доступен только администратору.")
            return redirect("dashboard")
        return view(request, *args, **kwargs)

    return wrapper


def editor_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.can_edit:
            messages.error(request, "Недостаточно прав для изменения данных.")
            return redirect("dashboard")
        return view(request, *args, **kwargs)

    return wrapper


class FSLoginView(LoginView):
    template_name = "login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class FSLogoutView(LogoutView):
    next_page = "login"


def _query_without_page(request):
    params = request.GET.copy()
    params.pop("page", None)
    return params.urlencode()


def _status_bars(stats):
    labels = dict(Client.Status.choices)
    palette = {
        "active": "ok",
        "inactive": "muted",
        "watch": "warn",
        "checking": "info",
        "blocked": "danger",
    }
    total = stats["total"] or 1
    return [
        {
            "code": row["status"],
            "label": labels.get(row["status"], row["status"]),
            "count": row["count"],
            "percent": round(row["count"] * 100 / total),
            "tone": palette.get(row["status"], "info"),
        }
        for row in stats["by_status"]
    ]


def _risk_bars(stats):
    labels = dict(Client.Risk.choices)
    tones = {"low": "ok", "medium": "warn", "high": "danger", "critical": "critical"}
    total = stats["total"] or 1
    return [
        {
            "code": row["risk_level"],
            "label": labels.get(row["risk_level"], row["risk_level"]),
            "count": row["count"],
            "percent": round(row["count"] * 100 / total),
            "tone": tones.get(row["risk_level"], "info"),
        }
        for row in stats["by_risk"]
    ]


@login_required
def dashboard(request):
    stats = services.client_stats()
    recent_clients = (
        Client.objects.filter(is_deleted=False)
        .select_related("source")
        .order_by("-created_at")[:7]
    )
    recent_events = (
        DataEvent.objects.select_related("client", "created_by", "source").order_by("-occurred_at")[:8]
    )
    week_ago = timezone.now() - timedelta(days=7)
    recent_audit = AuditLog.objects.select_related("user").order_by("-created_at")[:6]
    context = {
        "active_nav": "dashboard",
        "stats": stats,
        "status_bars": _status_bars(stats),
        "risk_bars": _risk_bars(stats),
        "recent_clients": recent_clients,
        "recent_events": recent_events,
        "recent_audit": recent_audit,
        "week_new": stats["new_week"],
        "week_ago": week_ago,
    }
    return render(request, "dashboard.html", context)


@login_required
def client_list(request):
    qs = Client.objects.filter(is_deleted=False).select_related("source").prefetch_related("contacts")
    qs = services.apply_filters(qs, request.GET)
    ordering = request.GET.get("ordering", "-updated_at")
    if ordering in {"last_name", "-last_name", "created_at", "-created_at", "updated_at", "-updated_at"}:
        qs = qs.order_by(ordering)
    paginator = Paginator(qs, 15)
    page = paginator.get_page(request.GET.get("page"))
    context = {
        "active_nav": "clients",
        "page_obj": page,
        "total": qs.count(),
        "search": request.GET.get("search", ""),
        "status": request.GET.get("status", ""),
        "risk_level": request.GET.get("risk_level", ""),
        "status_choices": Client.Status.choices,
        "risk_choices": Client.Risk.choices,
        "querystring": _query_without_page(request),
        "ordering": ordering,
    }
    return render(request, "clients/list.html", context)


@login_required
def client_detail(request, pk):
    client = get_object_or_404(
        Client.objects.select_related("source", "created_by").prefetch_related(
            "contacts", "data_items", "events__created_by", "documents", "consents"
        ),
        pk=pk,
        is_deleted=False,
    )
    services.log_action(request, AuditLog.Action.VIEW, client, model_name="Client")

    contact_form = ContactForm()
    data_form = ClientDataForm()
    event_form = EventForm()
    document_form = DocumentForm()
    consent_form = ConsentForm()

    if request.method == "POST":
        if not request.user.can_edit:
            return HttpResponseForbidden("Недостаточно прав")
        action = request.POST.get("action")
        if action == "contact_add":
            contact_form = ContactForm(request.POST)
            if contact_form.is_valid():
                contact_form.save(commit=False)
                contact = contact_form.instance
                contact.client = client
                contact.save()
                messages.success(request, "Контакт добавлен.")
                return redirect(f"{reverse('client_detail', args=[pk])}#contacts")
        elif action == "contact_delete":
            ClientContact.objects.filter(pk=request.POST.get("contact_id"), client=client).delete()
            messages.success(request, "Контакт удалён.")
            return redirect(f"{reverse('client_detail', args=[pk])}#contacts")
        elif action == "data_add":
            data_form = ClientDataForm(request.POST)
            if data_form.is_valid():
                item = data_form.save(commit=False)
                item.client = client
                item.save()
                messages.success(request, "Сведения добавлены.")
                return redirect(f"{reverse('client_detail', args=[pk])}#data")
        elif action == "event_add":
            event_form = EventForm(request.POST)
            if event_form.is_valid():
                event = event_form.save(commit=False)
                event.client = client
                event.created_by = request.user
                event.save()
                messages.success(request, "Событие добавлено.")
                return redirect(f"{reverse('client_detail', args=[pk])}#events")
        elif action == "document_add":
            document_form = DocumentForm(request.POST, request.FILES)
            if document_form.is_valid():
                document = document_form.save(commit=False)
                document.client = client
                document.uploaded_by = request.user
                document.save()
                messages.success(request, "Документ загружен.")
                return redirect(f"{reverse('client_detail', args=[pk])}#documents")
        elif action == "consent_add":
            consent_form = ConsentForm(request.POST)
            if consent_form.is_valid():
                consent = consent_form.save(commit=False)
                consent.client = client
                consent.save()
                messages.success(request, "Согласие сохранено.")
                return redirect(f"{reverse('client_detail', args=[pk])}#consents")

    context = {
        "active_nav": "clients",
        "client": client,
        "contact_form": contact_form,
        "data_form": data_form,
        "event_form": event_form,
        "document_form": document_form,
        "consent_form": consent_form,
        "contacts": client.contacts.all(),
        "data_items": client.data_items.all(),
        "events": client.events.all()[:40],
        "documents": client.documents.all(),
        "consents": client.consents.all(),
    }
    return render(request, "clients/detail.html", context)


@editor_required
def client_create(request):
    form = ClientForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        client = form.save(commit=False)
        client.created_by = request.user
        client.save()
        DataEvent.objects.create(
            client=client,
            event_type=DataEvent.Kind.UPDATE,
            title="Запись создана через веб-интерфейс",
            created_by=request.user,
        )
        services.log_action(request, AuditLog.Action.CREATE, client, model_name="Client")
        messages.success(request, f"Запись «{client.full_name}» создана.")
        return redirect("client_detail", pk=client.pk)
    return render(request, "clients/form.html", {"active_nav": "clients", "form": form, "client": None})


@editor_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk, is_deleted=False)
    form = ClientForm(request.POST or None, request.FILES or None, instance=client)
    if request.method == "POST" and form.is_valid():
        client = form.save()
        services.log_action(request, AuditLog.Action.UPDATE, client, model_name="Client")
        messages.success(request, "Изменения сохранены.")
        return redirect("client_detail", pk=client.pk)
    return render(
        request,
        "clients/form.html",
        {"active_nav": "clients", "form": form, "client": client},
    )


@require_POST
@editor_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    client.is_deleted = True
    client.deleted_at = timezone.now()
    client.save(update_fields=["is_deleted", "deleted_at"])
    services.log_action(request, AuditLog.Action.DELETE, client, model_name="Client")
    messages.success(request, "Запись перемещена в архив.")
    return redirect("client_list")


@editor_required
def import_view(request):
    form = ImportForm(request.POST or None, request.FILES or None)
    result = None
    errors = []
    if request.method == "POST" and form.is_valid():
        upload = form.cleaned_data["file"]
        source = form.cleaned_data.get("source")
        try:
            rows = services.parse_import_file(upload)
            created, errors = services.import_clients(rows, request.user, source)
            result = {"created": created, "total": len(rows)}
            services.log_action(
                request,
                AuditLog.Action.IMPORT,
                model_name="Client",
                details={"created": created, "errors": len(errors), "filename": upload.name},
            )
            messages.success(request, f"Импорт завершён: добавлено {created} из {len(rows)} строк.")
        except Exception as exc:
            messages.error(request, f"Ошибка импорта: {exc}")
    return render(
        request,
        "clients/import.html",
        {"active_nav": "clients", "form": form, "result": result, "errors": errors[:30]},
    )


@login_required
def export_clients(request):
    qs = services.apply_filters(Client.objects.filter(is_deleted=False), request.GET)
    csv_text = services.clients_to_csv(qs)
    services.log_action(request, AuditLog.Action.EXPORT, model_name="Client", details={"count": qs.count()})
    response = HttpResponse(csv_text, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="fsb_clients_{timezone.now():%Y%m%d_%H%M}.csv"'
    return response


@login_required
def audit_list(request):
    qs = AuditLog.objects.select_related("user")
    action = request.GET.get("action", "")
    search = request.GET.get("search", "").strip()
    if action:
        qs = qs.filter(action=action)
    if search:
        qs = qs.filter(
            Q(object_repr__icontains=search)
            | Q(user__username__icontains=search)
            | Q(user__full_name__icontains=search)
            | Q(model_name__icontains=search)
        )
    paginator = Paginator(qs, 30)
    page = paginator.get_page(request.GET.get("page"))
    context = {
        "active_nav": "audit",
        "page_obj": page,
        "action": action,
        "search": search,
        "action_choices": AuditLog.Action.choices,
        "total": qs.count(),
        "querystring": _query_without_page(request),
    }
    return render(request, "audit.html", context)


@login_required
def sources(request):
    form = DataSourceForm()
    if request.method == "POST":
        if not request.user.can_edit:
            return HttpResponseForbidden("Недостаточно прав")
        form = DataSourceForm(request.POST)
        if form.is_valid():
            source = form.save()
            services.log_action(request, AuditLog.Action.CREATE, source, model_name="DataSource")
            messages.success(request, "Источник добавлен.")
            return redirect("sources")
    items = DataSource.objects.annotate(
        clients_count=Count("clients", filter=Q(clients__is_deleted=False))
    ).order_by("name")
    return render(
        request,
        "sources.html",
        {"active_nav": "sources", "form": form, "items": items},
    )


@admin_required
def users_view(request):
    form = UserForm()
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            services.log_action(request, AuditLog.Action.CREATE, user, model_name="User")
            messages.success(request, f"Сотрудник {user.display_name} добавлен.")
            return redirect("users")
    items = User.objects.select_related("role").order_by("username")
    return render(
        request,
        "users.html",
        {"active_nav": "users", "form": form, "items": items},
    )


@require_POST
@admin_required
def user_toggle(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "Нельзя заблокировать собственную учётную запись.")
        return redirect("users")
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    services.log_action(
        request,
        AuditLog.Action.UPDATE,
        user,
        model_name="User",
        details={"is_active": user.is_active},
    )
    messages.success(request, "Статус сотрудника обновлён.")
    return redirect("users")


@login_required
def reports_view(request):
    stats = services.client_stats()
    context = {
        "active_nav": "reports",
        "stats": stats,
        "status_bars": _status_bars(stats),
        "risk_bars": _risk_bars(stats),
        "sources": DataSource.objects.annotate(
            clients_count=Count("clients", filter=Q(clients__is_deleted=False))
        ).order_by("-clients_count"),
        "recent": Client.objects.filter(is_deleted=False).order_by("-created_at")[:5],
        "reports": request.user.reports.select_related("created_by")[:10] if request.user.is_authenticated else [],
    }
    return render(request, "reports.html", context)


@login_required
def profile_view(request):
    return render(request, "profile.html", {"active_nav": "profile"})
