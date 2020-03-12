from django.conf import settings
from django.db import models


# Create your models here.
class OperationManager(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    phone_no = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return "{}: {}".format(self.id, self.name)

    @property
    def name(self):
        return self.user.get_full_name()
