from django.contrib import admin

from Halanx.admin import halanxhomes_admin
from Homes.Bookings.models import Booking, FacilityItem, BookingFacility, MonthlyRent, AdvanceBooking, \
    BookingMoveInDigitalSignature
from Homes.Bookings.utils import load_rent_agreement


# noinspection PyUnusedLocal

def export_rent_agreement(modeladmin, request, queryset):
    obj = queryset.first()
    if obj:
        return load_rent_agreement(obj)


export_rent_agreement.short_description = u"Export Rent Agreement"


@admin.register(FacilityItem, site=halanxhomes_admin)
class FacilityItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type')
    list_filter = ('type',)

    class Meta:
        model = FacilityItem


class BookingFacilityInline(admin.TabularInline):
    readonly_fields = ('facility_type',)
    model = BookingFacility
    extra = 0
    show_change_link = True

    @staticmethod
    def facility_type(obj):
        return obj.item.get_type_display()


class BookingMoveInDigitalSignatureInline(admin.TabularInline):
    model = BookingMoveInDigitalSignature
    extra = 0


@admin.register(Booking, site=halanxhomes_admin)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'status', 'created_at', 'modified_at', 'license_start_date', 'moved_out')
    search_fields = ('tenant__customer__user__first_name', 'tenant__customer__phone_no')
    inlines = (BookingFacilityInline, BookingMoveInDigitalSignatureInline)
    actions = (export_rent_agreement,)
    raw_id_fields = ('tenant', 'space')
    list_filter = ('status',)

    class Meta:
        model = Booking


@admin.register(MonthlyRent, site=halanxhomes_admin)
class MonthlyRentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'tenant_name', 'start_date', 'rent', 'status')
    search_fields = ('booking__tenant__customer__user__first_name', 'booking__tenant__customer__phone_no',
                     'booking__id')
    raw_id_fields = ('booking', 'payment')
    list_filter = ('status',)

    class Meta:
        model = MonthlyRent

    @staticmethod
    def tenant_name(obj):
        if obj.booking:
            return obj.booking.tenant.name


@admin.register(AdvanceBooking, site=halanxhomes_admin)
class AdvanceBookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'created_at', 'modified_at')
    search_fields = ('tenant__customer__user__first_name', 'tenant__customer__phone_no')
    raw_id_fields = ('tenant',)
    list_filter = ('cancelled',)

    class Meta:
        model = AdvanceBooking
