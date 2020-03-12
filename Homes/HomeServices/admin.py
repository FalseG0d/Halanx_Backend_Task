from django.contrib import admin

from Halanx.admin import halanxhomes_admin
from Homes.HomeServices.models import ServiceCategory, ServiceRequest, SupportStaffMember, MajorServiceCategory, \
    ServiceRequestImage, SupportStaffMemberMajorService, SupportStaffMemberWorkAddressDetail


@admin.register(MajorServiceCategory, site=halanxhomes_admin)
class ServiceCategoryModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

    class Meta:
        model = MajorServiceCategory


@admin.register(ServiceCategory, site=halanxhomes_admin)
class ServiceCategoryModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'parent')

    class Meta:
        model = ServiceCategory


@admin.register(ServiceRequest, site=halanxhomes_admin)
class ServiceRequestModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'booking', 'created_at', 'support_staff_member', 'status')

    class Meta:
        model = ServiceRequest


class SupportStaffMemberMajorServiceInline(admin.TabularInline):
    model = SupportStaffMemberMajorService
    extra = 2


class SupportStaffMemberWorkAddressDetailInline(admin.StackedInline):
    model = SupportStaffMemberWorkAddressDetail
    extra = 0


@admin.register(SupportStaffMember, site=halanxhomes_admin)
class SupportStaffMemberModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone_no')
    inlines = (SupportStaffMemberMajorServiceInline, SupportStaffMemberWorkAddressDetailInline)

    class Meta:
        model = SupportStaffMember


@admin.register(ServiceRequestImage, site=halanxhomes_admin)
class ServiceRequestImageModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_image_html',)

    class Meta:
        model = ServiceRequestImage
