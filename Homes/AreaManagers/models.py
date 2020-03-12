from django.db import models
from django.conf import settings

from Homes.AreaManagers.utils import get_area_manager_profile_pic_upload_path


class AreaManager(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    phone_no = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(blank=True, null=True, max_length=300)
    area = models.CharField(blank=True, null=True, max_length=300)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    radius = models.FloatField(blank=True, null=True, help_text='In km.')
    profile_pic = models.ImageField(upload_to=get_area_manager_profile_pic_upload_path, null=True, blank=True)

    def __str__(self):
        return "{}: {}".format(self.id, self.name)

    @property
    def name(self):
        return self.user.get_full_name()
