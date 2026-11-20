from core.models import Client, DataSource

ROLE_LABELS = {
    "admin": "Администратор",
    "operator": "Оператор",
    "analyst": "Аналитик",
    "viewer": "Наблюдатель",
}


def navigation(request):
    """Shared context for the web interface."""
    context = {
        "role_labels": ROLE_LABELS,
        "nav_sources_count": DataSource.objects.filter(is_active=True).count(),
    }
    if request.user.is_authenticated:
        context["nav_clients_count"] = Client.objects.filter(is_deleted=False).count()
    return context
