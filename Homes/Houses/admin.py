from datetime import datetime

from django.contrib import admin

from Halanx.admin import halanxhomes_admin
from Homes.Houses.models import (House, HousePicture, HouseMonthlyExpense, HouseAmenity, Amenity, SubAmenity,
                                 HouseVisit, MonthlyExpenseCategory, Space, Flat, PrivateRoom, SharedRoom,
                                 HouseAddressDetail, Bed, HouseApplication, HouseApplicationAddressDetail,
                                 HouseSearchSlug, PopularLocation, SampleData,
                                 HouseFurnishingBill, HouseFurnishingItem, ExistingFacility, SpaceSubType, Occupation,
                                 BillSplit, Bill, BillCategory)

from Homes.Houses.utils import ExistingFacilityChoices
from utility.file_utils import render_pdf_from_html


def export_service_agreement(modeladmin, request, queryset):
    obj = queryset.first()
    if obj:
        existing_facilities = {}
        for category, _ in ExistingFacilityChoices:
            existing_facilities[category] = ", ".join(str(facility) for facility in
                                                      obj.existing_facilities.filter(type=category))
        return render_pdf_from_html("service_agreement.html", {'owner': obj.owner, 'house': obj,
                                                               'agreement_date': datetime.now().date().strftime(
                                                                   "%d %b, %Y"),
                                                               'existing_facilities': existing_facilities,
                                                               'site': 'https://d28fujbigzf56k.cloudfront.net'},
                                    '{}_Service_Agreement.pdf'.format(obj.owner.name.replace(' ', '_')))


export_service_agreement.short_description = u"Export Service Agreement"


def download_house_furnishing_bill(modeladmin, request, queryset):
    obj = queryset.first()
    if obj:
        return render_pdf_from_html("house_furnishing_bill.html", {'owner': obj.house.owner, 'bill': obj,
                                                                   'items': obj.items.all()},
                                    'Furnishing_Invoice_{}.pdf'.format(obj.id))


download_house_furnishing_bill.short_description = u"Download house furnishing bill"


class HouseApplicationAddressDetailInline(admin.StackedInline):
    model = HouseApplicationAddressDetail


@admin.register(HouseApplication, site=halanxhomes_admin)
class HouseApplicationModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'plan', 'owner')

    class Meta:
        model = HouseApplication

    inlines = (
        HouseApplicationAddressDetailInline,
    )

    def get_inline_instances(self, request, obj=None):
        # Return no inlines when obj is being created
        if not obj:
            return []
        else:
            return super(HouseApplicationModelAdmin, self).get_inline_instances(request, obj)


@admin.register(HouseVisit, site=halanxhomes_admin)
class HouseVisitModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'house', 'customer', 'scheduled_visit_time', 'area_manager', 'visited', 'cancelled')
    raw_id_fields = ('customer', 'house', 'area_manager')
    search_fields = ('customer__user__first_name', 'customer__phone_no', 'house__name')
    list_filter = ('visited', 'cancelled')

    class Meta:
        model = HouseVisit


@admin.register(Amenity, site=halanxhomes_admin)
class AmenityModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'get_amenity_image_html', 'is_major')
    readonly_fields = ('get_amenity_image_html',)

    class Meta:
        model = Amenity


@admin.register(SubAmenity, site=halanxhomes_admin)
class SubAmenityModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'get_sub_amenity_image_html')
    readonly_fields = ('get_sub_amenity_image_html',)

    class Meta:
        model = SubAmenity


@admin.register(MonthlyExpenseCategory, site=halanxhomes_admin)
class MonthlyExpenseCategoryModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'get_expense_category_image_html')

    class Meta:
        model = MonthlyExpenseCategory


class HouseAddressDetailInline(admin.StackedInline):
    model = HouseAddressDetail


class HousePictureInline(admin.TabularInline):
    model = HousePicture
    extra = 0


class HouseInline(admin.TabularInline):
    model = House
    extra = 0


class HouseAmenityInline(admin.TabularInline):
    model = HouseAmenity
    extra = 0


class ExistingFacilityInline(admin.TabularInline):
    model = ExistingFacility
    extra = 0


class HouseMonthlyExpenseInline(admin.TabularInline):
    model = HouseMonthlyExpense
    extra = 0


class FlatInline(admin.TabularInline):
    model = Flat
    extra = 0


class SharedRoomInline(admin.TabularInline):
    readonly_fields = ('id', 'bed_count', 'free_bed_count')
    model = SharedRoom
    extra = 0
    show_change_link = True

    @staticmethod
    def free_bed_count(obj):
        return obj.free_bed_count


class PrivateRoomInline(admin.TabularInline):
    model = PrivateRoom
    extra = 0


class BedInline(admin.TabularInline):
    model = Bed
    extra = 0


@admin.register(House, site=halanxhomes_admin)
class HouseModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'available', 'bhk_count', 'location', 'visible')
    raw_id_fields = ('owner',)
    search_fields = ('name', 'owner__user__first_name')
    list_filter = ('bhk_count', 'house_type', 'furnish_type', 'available_accomodation_types',
                   'accomodation_allowed', 'visible')
    actions = (export_service_agreement,)

    class Meta:
        model = House

    inlines = (
        HouseAddressDetailInline,
        HousePictureInline,
        HouseAmenityInline,
        ExistingFacilityInline,
        HouseMonthlyExpenseInline,
    )

    @staticmethod
    def location(obj):
        return "{}, {}".format(obj.address.city, obj.address.state)

    def get_inline_instances(self, request, obj=None):
        # Return no inlines when obj is being created
        if not obj:
            return []
        else:
            return super(HouseModelAdmin, self).get_inline_instances(request, obj)


@admin.register(Space, site=halanxhomes_admin)
class SpaceModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'house', 'name', 'type', 'subtype', 'availability', 'visible')
    raw_id_fields = ('house', 'subtype')
    search_fields = ('house__id',)
    list_filter = ('type', 'subtype', 'availability')

    class Meta:
        model = Space

    inlines = (
        FlatInline,
        PrivateRoomInline,
        SharedRoomInline,
    )


@admin.register(SpaceSubType, site=halanxhomes_admin)
class SpaceSubTypeModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'parent_type')

    class Meta:
        model = SpaceSubType


@admin.register(Flat, site=halanxhomes_admin)
class FlatModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'space')

    class Meta:
        model = Flat


@admin.register(PrivateRoom, site=halanxhomes_admin)
class PrivateRoomModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'space')

    class Meta:
        model = PrivateRoom


@admin.register(SharedRoom, site=halanxhomes_admin)
class SharedRoomModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'space', 'bed_count')

    class Meta:
        model = SharedRoom

    inlines = (
        BedInline,
    )


class HouseFurnishingItemInline(admin.TabularInline):
    model = HouseFurnishingItem
    extra = 0


@admin.register(HouseFurnishingBill, site=halanxhomes_admin)
class HouseFurnishingBillAdmin(admin.ModelAdmin):
    list_display = ('id', 'house', 'timestamp', 'total', 'cleared')
    actions = (download_house_furnishing_bill,)

    class Meta:
        model = HouseFurnishingBill

    inlines = (
        HouseFurnishingItemInline,
    )


@admin.register(HouseSearchSlug, site=halanxhomes_admin)
class HouseSearchSlugAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'created_at', 'updated_at')


@admin.register(PopularLocation, site=halanxhomes_admin)
class PopularLocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'latitude', 'longitude', 'city', 'state')


@admin.register(SampleData, site=halanxhomes_admin)
class SampleDataModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'query_params', 'body_data')


@admin.register(Occupation, site=halanxhomes_admin)
class OccupationModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(BillCategory, site=halanxhomes_admin)
class BillCategoryModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Bill, site=halanxhomes_admin)
class BillModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'house', 'amount', 'paid', 'due_date', 'category')
    raw_id_fields = ('owner', )


@admin.register(BillSplit, site=halanxhomes_admin)
class BillSplitModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'paid', 'tenant')

# @admin.register(HouseReview, site=halanxhomes_admin)
# class HouseReviewModelAdmin(admin.ModelAdmin):
#     list_display = ('id', 'content', 'rating', 'tenant')