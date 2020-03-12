from django.contrib import admin

from Common.utils import PaymentStatusCategories
from Halanx.admin import halanxhomes_admin
from Homes.Houses.models import House
from Homes.Owners.models import Owner, OwnerDocument, OwnerWallet, OwnerPayment, OwnerAddressDetail, OwnerBankDetail, \
    OwnerListing, OwnerNotification, OwnerMonthlyEarning, WithdrawalRequest, TeamMember, Vendor, TenantGroup


class OwnerDocumentInline(admin.TabularInline):
    model = OwnerDocument
    extra = 0


class OwnerWalletInline(admin.StackedInline):
    model = OwnerWallet


class OwnerAddressDetailInline(admin.StackedInline):
    model = OwnerAddressDetail


class OwnerBankDetailInline(admin.StackedInline):
    model = OwnerBankDetail


class HouseInline(admin.TabularInline):
    fields = ('id', 'name', 'available', 'visible', 'bhk_count', 'house_type', 'furnish_type')
    model = House
    extra = 0
    show_change_link = True
    verbose_name_plural = "Owned Houses"

    fk_name = 'owner'


class ManagedHouseInline(admin.TabularInline):
    fields = ('id', 'name', 'available', 'visible', 'bhk_count', 'house_type', 'furnish_type')
    model = House
    extra = 0
    show_change_link = True
    verbose_name_plural = "Managed Houses"
    fk_name = 'managed_by'


@admin.register(Owner, site=halanxhomes_admin)
class OwnerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'verified', 'location')
    raw_id_fields = ('user', 'referrer')
    search_fields = ('user__first_name', 'phone_no')
    list_filter = ('verified',)

    inlines = (
        OwnerAddressDetailInline,
        OwnerBankDetailInline,
        OwnerWalletInline,
        OwnerDocumentInline,
        HouseInline,
        ManagedHouseInline
    )

    @staticmethod
    def location(obj):
        return "{}, {}".format(obj.address.city, obj.address.state)

    def get_inline_instances(self, request, obj=None):
        # Return no inlines when obj is being created
        if not obj:
            return []
        else:
            return super(OwnerAdmin, self).get_inline_instances(request, obj)


@admin.register(OwnerWallet, site=halanxhomes_admin)
class OwnerWalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner')
    search_fields = ('owner__user__first_name', 'owner__phone_no')


@admin.register(OwnerPayment, site=halanxhomes_admin)
class OwnerPaymentModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'wallet', 'user', 'amount', 'type', 'status')
    search_fields = ('wallet__owner__user__first_name', 'wallet__owner__phone_no')
    list_filter = ('type', 'status',)
    raw_id_fields = ('user', 'wallet')


class WithdrawalRequestListFilter(admin.SimpleListFilter):
    title = 'status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return PaymentStatusCategories

    def queryset(self, request, queryset):
        return queryset.filter(payment__status=self.value()) if self.value() else queryset


@admin.register(WithdrawalRequest, site=halanxhomes_admin)
class WithdrawalRequestModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'created_at', 'amount', 'status')
    search_fields = ('owner__user__first_name', 'owner__phone_no')
    list_filter = (WithdrawalRequestListFilter,)
    raw_id_fields = ('owner', 'payment')


@admin.register(OwnerNotification, site=halanxhomes_admin)
class OwnerNotificationModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'timestamp', 'category', 'title')


@admin.register(OwnerMonthlyEarning, site=halanxhomes_admin)
class OwnerMonthlyEarningModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'start_date', 'end_date', 'rent', 'total', 'credited')


@admin.register(OwnerListing, site=halanxhomes_admin)
class OwnerListingModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone_no', 'bhk_count')


@admin.register(TeamMember, site=halanxhomes_admin)
class TeamMemberModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone_no', 'name', 'about', 'email', 'owner')


@admin.register(Vendor, site=halanxhomes_admin)
class VendorModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone_no', 'occupation', 'owner')


@admin.register(TenantGroup, site=halanxhomes_admin)
class TenantGroupModelAdmin(admin.ModelAdmin):
    raw_id_fields = ('tenants', 'owner')
    list_display = ('owner', )