from rest_framework.compat import is_authenticated
from rest_framework.permissions import BasePermission

from Homes.AreaManagers.models import AreaManager


class IsAreaManager(BasePermission):
    """
    Allows access only to area managers.
    """

    def has_permission(self, request, view):
        return request.user and is_authenticated(request.user) and AreaManager.objects.filter(user=request.user).count()
