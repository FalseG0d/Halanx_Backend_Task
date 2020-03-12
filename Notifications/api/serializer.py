from rest_framework import serializers

from Notifications.models import Notification, NotificationImage
from utility.serializers import DateTimeFieldTZ
from utility.time_utils import get_natural_datetime


class NotificationListSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    timestamp = DateTimeFieldTZ()

    class Meta:
        model = Notification
        fields = ('target', 'category', 'content', 'timestamp', 'image', 'payload')

    @staticmethod
    def get_image(obj):
        notif_image = NotificationImage.objects.filter(category=obj.category).first()
        return notif_image.image.url if notif_image else None

    @staticmethod
    def get_timestamp(obj):
        return get_natural_datetime(obj.timestamp)
