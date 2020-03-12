from django.contrib import admin

from Halanx.admin import halanxhomes_admin
from Homes.Tenants.models import Tenant, TenantDocument, TenantWallet, TenantPayment, TenantPermanentAddressDetail, \
    TenantMoveOutRequest, \
    TenantBankDetail, TenantCompanyAddressDetail, TenantRequirement, TenantLateCheckin, TenantMeal


class TenantDocumentInline(admin.TabularInline):
    model = TenantDocument
    extra = 1


class TenantWalletInline(admin.StackedInline):
    model = TenantWallet


class TenantPermanentAddressDetailInline(admin.StackedInline):
    model = TenantPermanentAddressDetail


class TenantCompanyAddressDetailInline(admin.StackedInline):
    model = TenantCompanyAddressDetail


class TenantBankDetailInline(admin.StackedInline):
    model = TenantBankDetail


@admin.register(Tenant, site=halanxhomes_admin)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    search_fields = ('customer__user__username', 'customer__user__first_name')
    raw_id_fields = ('customer', 'referrer')

    inlines = (
        TenantWalletInline,
        TenantPermanentAddressDetailInline,
        TenantDocumentInline,
        TenantCompanyAddressDetailInline,
        TenantBankDetailInline,
    )

    def get_inline_instances(self, request, obj=None):
        # Return no inlines when obj is being created
        if not obj:
            return []
        else:
            return super(TenantAdmin, self).get_inline_instances(request, obj)


@admin.register(TenantPayment, site=halanxhomes_admin)
class TenantPaymentModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'wallet', 'user', 'amount', 'category', 'type', 'status', 'payment_gateway')
    list_filter = ('status', 'type', 'category')
    search_fields = ('wallet__tenant__customer__user__first_name',)
    raw_id_fields = ('user', 'wallet', 'transaction', 'booking')

    @staticmethod
    def payment_gateway(obj):
        if obj.transaction:
            return obj.transaction.payment_gateway


@admin.register(TenantWallet, site=halanxhomes_admin)
class TenantWalletModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant')
    search_fields = ('tenant__customer__user__username', 'tenant__customer__user__first_name')
    raw_id_fields = ('tenant',)


@admin.register(TenantRequirement, site=halanxhomes_admin)
class TenantRequirementAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone_no', 'created_at',)
    raw_id_fields = ('tenant',)


@admin.register(TenantMoveOutRequest, site=halanxhomes_admin)
class TenantMoveOutRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'timing', 'created_at', 'get_name')
    raw_id_fields = ('tenant',)

    def get_name(self, obj):
        print(obj)
        return obj.tenant.name

    get_name.short_description = 'Tenant Name'
    get_name.admin_order_field = 'tenant__customer__user__first_name'


# @admin.register(TenantMoveInRequest, site=halanxhomes_admin)
# class TenantMoveInRequestAdmin(admin.ModelAdmin):
#     list_display = ('id', 'tenant', 'timing', 'created_at', 'get_name')
#     raw_id_fields = ('tenant',)
#
#     def get_name(self, obj):
#         print(obj)
#         return obj.tenant.name
#
#     get_name.short_description = 'Tenant Name'
#     get_name.admin_order_field = 'tenant__customer__user__first_name'

@admin.register(TenantLateCheckin, site=halanxhomes_admin)
class TenantLateCheckinAdmin(admin.ModelAdmin):
    list_display = ('id', 'current_booking', 'expected_checkin')
    raw_id_fields = ('current_booking', )


@admin.register(TenantMeal, site=halanxhomes_admin)
class TenantMealAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'date', 'having', 'house')
    raw_id_fields = ('accepted_by', )
