from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe

from Common.models import AddressDetail
from Homes.HomeServices.utils import (ServiceRequestStatusCategories, SR_NOT_RESOLVED,
                                      get_service_category_picture_upload_path,
                                      get_support_staff_member_picture_upload_path,
                                      get_major_service_category_picture_upload_path,
                                      get_service_request_picture_upload_path)


class MajorServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to=get_major_service_category_picture_upload_path, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Major service categories'

    def __str__(self):
        return str(self.name)


class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to=get_service_category_picture_upload_path, null=True, blank=True)
    parent = models.ForeignKey('MajorServiceCategory', blank=True, null=True, related_name='sub_categories')

    class Meta:
        verbose_name_plural = 'Service categories'

    def __str__(self):
        return str(self.name)


class ServiceRequest(models.Model):
    booking = models.ForeignKey('Bookings.Booking', on_delete=models.SET_NULL, null=True,
                                related_name='service_requests')
    category = models.ForeignKey('ServiceCategory', blank=True, null=True, related_name='service_requests')
    problem = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=30, default=SR_NOT_RESOLVED, choices=ServiceRequestStatusCategories)
    support_staff_member = models.ForeignKey('SupportStaffMember', blank=True, null=True,
                                             related_name='service_requests')
    remark = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_at = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return str(self.id)


class ServiceRequestImage(models.Model):
    image = models.ImageField(upload_to=get_service_request_picture_upload_path)
    service_request = models.ForeignKey(ServiceRequest, null=True, blank=True, related_name='images')

    def get_image_html(self):
        if self.image:
            return mark_safe('<img src="{}" />'.format(self.image.url))
        else:
            return None

    get_image_html.short_description = 'Image'
    get_image_html.allow_tags = True


class SupportStaffMember(models.Model):
    name = models.CharField(max_length=100)
    phone_no = models.CharField(max_length=15, blank=True, null=True)
    image = models.ImageField(upload_to=get_support_staff_member_picture_upload_path, null=True, blank=True)

    def __str__(self):
        return "{}: {}".format(self.id, self.name)

    def save(self, *args, **kwargs):
        if self.id is None:
            saved_image = self.image
            self.image = None
            super(SupportStaffMember, self).save(*args, **kwargs)
            self.image = saved_image
            kwargs.pop('force_insert', None)
            super(SupportStaffMember, self).save(*args, **kwargs)

    @property
    def categories(self):
        major_service_categories = self.staff_services.all().values_list('category')
        queryset = MajorServiceCategory.objects.filter(id__in=major_service_categories).distinct()
        return queryset


class SupportStaffMemberWorkAddressDetail(AddressDetail):
    staff_member = models.OneToOneField(SupportStaffMember, on_delete=models.CASCADE, related_name='work_address')


class SupportStaffMemberMajorService(models.Model):
    staff_member = models.ForeignKey(SupportStaffMember, on_delete=models.CASCADE, related_name='staff_services')
    category = models.ForeignKey(MajorServiceCategory, on_delete=models.CASCADE, related_name='staff_services')

    class Meta:
        unique_together = ('staff_member', 'category')


@receiver(post_save, sender=SupportStaffMember)
def support_staff_member_post_save_hook(sender, instance, created, **kwargs):
    if created:
        SupportStaffMemberWorkAddressDetail(staff_member=instance).save()
