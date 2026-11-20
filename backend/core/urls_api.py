from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from . import views_api

router = DefaultRouter()
router.register("clients", views_api.ClientViewSet, basename="client")
router.register("contacts", views_api.ClientContactViewSet, basename="contact")
router.register("client-data", views_api.ClientDataViewSet, basename="client-data")
router.register("events", views_api.DataEventViewSet, basename="event")
router.register("documents", views_api.DocumentViewSet, basename="document")
router.register("consents", views_api.ConsentViewSet, basename="consent")
router.register("sources", views_api.DataSourceViewSet, basename="source")
router.register("audit", views_api.AuditLogViewSet, basename="audit")
router.register("users", views_api.UserViewSet, basename="user")
router.register("roles", views_api.RoleViewSet, basename="role")
router.register("reports", views_api.ReportViewSet, basename="report")
router.register("integrations", views_api.IntegrationViewSet, basename="integration")

urlpatterns = [
    path("auth/login/", views_api.LoginView.as_view(), name="api_login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="api_refresh"),
    path("auth/verify/", TokenVerifyView.as_view(), name="api_verify"),
    path("auth/me/", views_api.MeView.as_view(), name="api_me"),
    path("stats/", views_api.StatsView.as_view(), name="api_stats"),
    path("", include(router.urls)),
]
