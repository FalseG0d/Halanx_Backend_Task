from rest_framework.exceptions import ValidationError

from Homes.OperationManagers.models import OperationManager
from Homes.Owners.models import Owner
from Homes.Tenants.models import Tenant


def is_user_a_owner(request, raise_exception=False):
    if not request.user.is_authenticated:
        if raise_exception:
            raise ValidationError({'detail': "User is not authenticated"})
        else:
            return None

    try:
        owner = Owner.objects.get(user=request.user)
        return owner
    except Owner.DoesNotExist:
        if raise_exception:
            raise ValidationError({'detail': 'Not found'})
        return None


def is_user_a_tenant(request, raise_exception=False):
    if not request.user.is_authenticated:
        if raise_exception:
            raise ValidationError("User is not authenticated")
        else:
            return None

    tenant = Tenant.objects.filter(customer__user=request.user).first()
    if tenant:
        return tenant
    else:
        if raise_exception:
            raise ValidationError({'detail': 'Not found'})
        return None


def is_user_an_operation_manager(request, raise_exception=False):
    if not request.user.is_authenticated:
        if raise_exception:
            raise ValidationError("User is not authenticated")
        else:
            return None

    operation_manager = OperationManager.objects.filter(user=request.user).first()
    if operation_manager:
        return operation_manager
    else:
        if raise_exception:
            raise ValidationError({'detail': 'Not found'})
        return None
