from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from . import services
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
from .permissions import IsAdminRole, IsEditorOrReadOnly
from .serializers import (
    AuditLogSerializer,
    ClientContactSerializer,
    ClientDataSerializer,
    ClientListSerializer,
    ClientSerializer,
    ConsentSerializer,
    DataEventSerializer,
    DataSourceSerializer,
    DocumentSerializer,
    FSBTokenObtainPairSerializer,
    IntegrationSerializer,
    ReportSerializer,
    RoleSerializer,
    UserSerializer,
)


class LoginView(TokenObtainPairView):
    serializer_class = FSBTokenObtainPairSerializer
    permission_classes = []

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            username = request.data.get("username", "")
            user = User.objects.filter(username=username).first()
            services.log_action(request, AuditLog.Action.LOGIN, user, model_name="User", details={"username": username}, actor=user)
        return response


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class StatsView(APIView):
    def get(self, request):
        return Response(services.client_stats())


class ClientViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsEditorOrReadOnly]

    def get_queryset(self):
        qs = (
            Client.objects.filter(is_deleted=False)
            .select_related("source", "created_by")
            .prefetch_related("contacts", "data_items", "events", "documents", "consents")
        )
        if self.action == "retrieve":
            return qs
        qs = services.apply_filters(qs, self.request.query_params)
        ordering = self.request.query_params.get("ordering")
        allowed = {"last_name", "-last_name", "created_at", "-created_at", "updated_at", "-updated_at", "risk_level"}
        if ordering in allowed:
            qs = qs.order_by(ordering)
        return qs

    def get_serializer_class(self):
        return ClientListSerializer if self.action == "list" else ClientSerializer

    def perform_create(self, serializer):
        client = serializer.save(created_by=self.request.user)
        DataEvent.objects.create(
            client=client,
            event_type=DataEvent.Kind.UPDATE,
            title="Запись создана",
            description=f"Сотрудник: {self.request.user.display_name}",
            created_by=self.request.user,
        )
        services.log_action(self.request, AuditLog.Action.CREATE, client, model_name="Client")

    def perform_update(self, serializer):
        client = serializer.save()
        services.log_action(self.request, AuditLog.Action.UPDATE, client, model_name="Client")

    def destroy(self, request, *args, **kwargs):
        client = self.get_object()
        client.is_deleted = True
        client.deleted_at = timezone.now()
        client.save(update_fields=["is_deleted", "deleted_at"])
        services.log_action(request, AuditLog.Action.DELETE, client, model_name="Client")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        return Response(services.client_stats())

    @action(detail=False, methods=["get"])
    def export(self, request):
        qs = services.apply_filters(Client.objects.filter(is_deleted=False), request.query_params)
        csv_text = services.clients_to_csv(qs)
        services.log_action(request, AuditLog.Action.EXPORT, model_name="Client", details={"count": qs.count()})
        response = HttpResponse(csv_text, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="fsb_clients_{timezone.now():%Y%m%d_%H%M}.csv"'
        return response

    @action(
        detail=False,
        methods=["post"],
        url_path="import",
        parser_classes=[MultiPartParser, FormParser],
    )
    def import_file(self, request):
        upload = request.FILES.get("file")
        if not upload:
            return Response({"detail": "Файл не передан"}, status=status.HTTP_400_BAD_REQUEST)
        source = None
        source_id = request.data.get("source")
        if source_id:
            source = DataSource.objects.filter(pk=source_id).first()
        try:
            rows = services.parse_import_file(upload)
        except Exception as exc:
            return Response({"detail": f"Не удалось прочитать файл: {exc}"}, status=status.HTTP_400_BAD_REQUEST)
        created, errors = services.import_clients(rows, request.user, source)
        services.log_action(
            request,
            AuditLog.Action.IMPORT,
            model_name="Client",
            details={"created": created, "errors": len(errors), "filename": upload.name},
        )
        return Response({"created": created, "errors": errors, "total_rows": len(rows)})


class ClientContactViewSet(viewsets.ModelViewSet):
    serializer_class = ClientContactSerializer
    permission_classes = [IsAuthenticated, IsEditorOrReadOnly]

    def get_queryset(self):
        qs = ClientContact.objects.select_related("client")
        client_id = self.request.query_params.get("client")
        return qs.filter(client_id=client_id) if client_id else qs

    def perform_create(self, serializer):
        contact = serializer.save()
        services.log_action(self.request, AuditLog.Action.UPDATE, contact.client, model_name="ClientContact")


class ClientDataViewSet(viewsets.ModelViewSet):
    serializer_class = ClientDataSerializer
    permission_classes = [IsAuthenticated, IsEditorOrReadOnly]

    def get_queryset(self):
        qs = ClientData.objects.select_related("client", "source")
        client_id = self.request.query_params.get("client")
        return qs.filter(client_id=client_id) if client_id else qs

    def perform_create(self, serializer):
        item = serializer.save()
        services.log_action(self.request, AuditLog.Action.UPDATE, item.client, model_name="ClientData")


class DataEventViewSet(viewsets.ModelViewSet):
    serializer_class = DataEventSerializer
    permission_classes = [IsAuthenticated, IsEditorOrReadOnly]

    def get_queryset(self):
        qs = DataEvent.objects.select_related("client", "source", "created_by")
        client_id = self.request.query_params.get("client")
        if client_id:
            qs = qs.filter(client_id=client_id)
        event_type = self.request.query_params.get("event_type")
        if event_type:
            qs = qs.filter(event_type=event_type)
        return qs

    def perform_create(self, serializer):
        event = serializer.save(created_by=self.request.user)
        services.log_action(self.request, AuditLog.Action.UPDATE, event.client, model_name="DataEvent")


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, IsEditorOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        qs = Document.objects.select_related("client", "uploaded_by")
        client_id = self.request.query_params.get("client")
        return qs.filter(client_id=client_id) if client_id else qs

    def perform_create(self, serializer):
        document = serializer.save(uploaded_by=self.request.user)
        services.log_action(self.request, AuditLog.Action.UPDATE, document.client, model_name="Document")


class ConsentViewSet(viewsets.ModelViewSet):
    serializer_class = ConsentSerializer
    permission_classes = [IsAuthenticated, IsEditorOrReadOnly]

    def get_queryset(self):
        qs = Consent.objects.select_related("client", "document")
        client_id = self.request.query_params.get("client")
        return qs.filter(client_id=client_id) if client_id else qs


class DataSourceViewSet(viewsets.ModelViewSet):
    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated, IsEditorOrReadOnly]

    def get_queryset(self):
        return DataSource.objects.annotate(
            clients_count=Count("clients", filter=Q(clients__is_deleted=False))
        ).order_by("name")

    def perform_create(self, serializer):
        source = serializer.save()
        services.log_action(self.request, AuditLog.Action.CREATE, source, model_name="DataSource")


class AuditLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user")
        action_filter = self.request.query_params.get("action")
        if action_filter:
            qs = qs.filter(action=action_filter)
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(object_repr__icontains=search) | Q(user__username__icontains=search) | Q(model_name__icontains=search)
            )
        return qs


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]
    queryset = User.objects.select_related("role").order_by("username")


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    queryset = Role.objects.all()


class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, IsEditorOrReadOnly]

    def get_queryset(self):
        return Report.objects.select_related("created_by")

    def perform_create(self, serializer):
        report = serializer.save(created_by=self.request.user)
        services.log_action(self.request, AuditLog.Action.CREATE, report, model_name="Report")


class IntegrationViewSet(viewsets.ModelViewSet):
    serializer_class = IntegrationSerializer
    permission_classes = [IsAdminRole]
    queryset = Integration.objects.all()
