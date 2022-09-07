from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS


class AdminOnlyPermission(permissions.BasePermission):
    """
    Права доступа: только админ.
    """

    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.is_admin) or request.user.is_staff


class AuthorModeratorAdminOrReadOnly(permissions.BasePermission):
    """"
    Права доступа: Автор, модератор или администратор.
    """

    def has_permission(self, request, view):
        return (request.method
                in SAFE_METHODS) or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS) or (
            (request.user == obj.author
                or request.user.is_moderator
                or request.user.is_admin)
        )


class AdminOrReadonly(permissions.BasePermission):
    """
    Права доступа:
    чтение для всех
    изменение только для администратор
    """

    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS) or (
            (request.user.is_authenticated and (
                (request.user.is_admin or request.user.is_staff)))
        )
