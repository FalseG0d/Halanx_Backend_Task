from rest_framework.permissions import BasePermission

from Homes.utils import is_user_a_owner, is_user_a_tenant, is_user_an_operation_manager


class IsOwner(BasePermission):
    """
    Allows access only to authenticated Owners.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        owner = is_user_a_owner(request, raise_exception=False)
        # print("owner is ", owner)
        if owner:
            return True
        else:
            return False


class IsTenant(BasePermission):
    """
    Allows access only to authenticated Owners.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        tenant = is_user_a_tenant(request, raise_exception=False)
        # print("tenant is ", tenant)
        if tenant:
            return True
        else:
            return False


class IsTenantOrIsOwner(BasePermission):
    def has_permission(self, request, view):
        return IsOwner.has_permission(self, request, view) or IsTenant.has_permission(self, request, view)


class IsOperationManager(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        operation_manager = is_user_an_operation_manager(request, raise_exception=False)
        if operation_manager:
            return True
        else:
            return False
