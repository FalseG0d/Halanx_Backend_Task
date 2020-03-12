from datetime import timedelta

from django.db import models
from django.utils import timezone
# from django_mysql.models import JSONField

from jsonfield import JSONField
# from django.contrib.postgres.fields import JSONField
from Notifications.utils import (get_notification_image_upload_path, NotificationCategories,
                                 create_message_title_and_body, send_customer_notification)


class Notification(models.Model):
    target = models.ForeignKey('UserBase.Customer', blank=True, related_name="notifications",
                               null=True, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)
    category = models.CharField(max_length=50, blank=True, null=True, choices=NotificationCategories)
    content = models.TextField(max_length=200, blank=True, null=True)
    seen = models.BooleanField(default=False)
    display = models.BooleanField(default=True)
    payload = JSONField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return str(self.target.phone_no)

    def save(self, data=None, *args, **kwargs):
        if not self.pk:
            # set title, content, payload and display
            title, content, payload, display = create_message_title_and_body(self.category, data=data)
            payload = kwargs.pop('payload', payload)  # if payload already exists
            content_ascii_format = content.encode('ascii', 'ignore').decode()

            # if user has got same notification in last 10 seconds, abort.
            if self.target.notifications.filter(timestamp__gte=timezone.now() - timedelta(seconds=10),
                                                content=content_ascii_format).count():
                return

            # send notification using gcm
            if self.target.receive_notification and self.target.gcm_id:
                send_customer_notification(self.target, title, content, self.category, payload)

            self.content = content_ascii_format
            self.display = display
        super(Notification, self).save(*args, **kwargs)


class NotificationImage(models.Model):
    image = models.ImageField(upload_to=get_notification_image_upload_path, null=True, blank=True)
    category = models.CharField(max_length=50, blank=True, null=True, choices=NotificationCategories)

    def __str__(self):
        return str(self.category)

    def get_notification_image_html(self):
        if self.image:
            return '<img src="{}" width="80" height="80" />'.format(self.image.url)
        else:
            return None

    get_notification_image_html.short_description = 'Notification Image'
    get_notification_image_html.allow_tags = True
