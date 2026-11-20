from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsEditorOrReadOnly(BasePermission):
    """Any authenticated employee can read, only admins/operators can modify."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.can_edit


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.role_code == "admin")
        )
