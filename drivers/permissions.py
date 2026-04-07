from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import BasePermission


class AuthenticatedReadWrite(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user
        if not (user and getattr(user, "is_authenticated", False)):
            raise NotAuthenticated("Authentication credentials were not provided.")
        return True
