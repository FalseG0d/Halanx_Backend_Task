from django.contrib import admin

from Halanx.admin import halanx_admin
from Notifications.models import Notification, NotificationImage


class NotificationModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'target', 'category', 'timestamp', 'content', 'payload']
    raw_id_fields = ['target', ]

    class Meta:
        model = Notification

    def get_queryset(self, request):
        return Notification.objects.select_related('target').all()


class NotificationImageModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'category', 'get_notification_image_html']
    readonly_fields = ['get_notification_image_html']

    class Meta:
        model = NotificationImage


halanx_admin.register(Notification, NotificationModelAdmin)
halanx_admin.register(NotificationImage, NotificationImageModelAdmin)
