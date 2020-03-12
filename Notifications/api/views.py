from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from Notifications.api.serializer import NotificationListSerializer
from Notifications.models import Notification


class NotificationSetPagination(PageNumberPagination):
    page_size = 15
    max_page_size = 100


@api_view(['GET'])
@authentication_classes((BasicAuthentication, TokenAuthentication))
@permission_classes((IsAuthenticated,))
def user_notifications(request):
    """
    get:
    Get list of all notifications of a customer
    """
    notifications = Notification.objects.filter(target__user=request.user, display=True)
    notifications.update(seen=True)
    paginator = NotificationSetPagination()
    notifications = paginator.paginate_queryset(notifications, request=request)
    serializer = NotificationListSerializer(notifications, many=True)
    return paginator.get_paginated_response(serializer.data)
