from django.urls import path

from . import views_web

urlpatterns = [
    path("", views_web.dashboard, name="dashboard"),
    path("login/", views_web.FSLoginView.as_view(), name="login"),
    path("logout/", views_web.FSLogoutView.as_view(), name="logout"),
    path("clients/", views_web.client_list, name="client_list"),
    path("clients/new/", views_web.client_create, name="client_create"),
    path("clients/import/", views_web.import_view, name="client_import"),
    path("clients/export/", views_web.export_clients, name="client_export"),
    path("clients/<int:pk>/", views_web.client_detail, name="client_detail"),
    path("clients/<int:pk>/edit/", views_web.client_edit, name="client_edit"),
    path("clients/<int:pk>/delete/", views_web.client_delete, name="client_delete"),
    path("audit/", views_web.audit_list, name="audit"),
    path("sources/", views_web.sources, name="sources"),
    path("users/", views_web.users_view, name="users"),
    path("users/<int:pk>/toggle/", views_web.user_toggle, name="user_toggle"),
    path("reports/", views_web.reports_view, name="reports"),
    path("profile/", views_web.profile_view, name="profile"),
]
