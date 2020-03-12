from django.contrib import admin

from Halanx.admin import halanx_admin, halanxhomes_admin
from Homes.Tenants.models import TenantPayment
from Transaction.models import CustomerTransaction, StoreTransaction, HouseOwnerTransaction
from Transaction.utils import get_transaction_status


# noinspection PyUnusedLocal
def refresh_transactions_status(modeladmin, request, queryset):
    for obj in queryset:
        obj.complete = get_transaction_status(obj)
        obj.save()


refresh_transactions_status.short_description = u"Refresh transactions status"


class TransactionAdmin(admin.ModelAdmin):
    actions = (refresh_transactions_status,)
    list_display = ('id', 'name', 'timestamp', 'payment_gateway', 'platform', 'amount', 'complete', 'cancelled', 'transaction_id')
    list_filter = ('complete', 'cancelled', 'payment_gateway', 'platform',)

    class Meta:
        abstract = True


class TenantPaymentTabularInline(admin.TabularInline):
    model = TenantPayment
    extra = 0
    fields = ('id', 'amount', 'original_amount', 'fine', 'discount', 'apply_cashback', 'status',)
    show_change_link = True


@admin.register(CustomerTransaction, site=halanxhomes_admin)
class CustomerTransactionAdmin(TransactionAdmin):
    raw_id_fields = ('customer', 'collector')
    search_fields = ('customer__user__first_name',)
    list_display = TransactionAdmin.list_display + ('customer', )

    inlines = [
        TenantPaymentTabularInline,
    ]

    class Meta:
        model = CustomerTransaction

    @staticmethod
    def name(obj):
        if obj.customer:
            return obj.customer.name


class StoreTransactionAdmin(TransactionAdmin):
    class Meta:
        model = StoreTransaction

    @staticmethod
    def name(obj):
        if obj.store:
            return obj.store.name


@admin.register(HouseOwnerTransaction, site=halanxhomes_admin)
class HouseOwnerTransactionAdmin(TransactionAdmin):
    class Meta:
        model = HouseOwnerTransaction

    @staticmethod
    def name(obj):
        if obj.owner:
            return obj.owner.name


halanx_admin.register(CustomerTransaction, CustomerTransactionAdmin)
halanx_admin.register(StoreTransaction, StoreTransactionAdmin)
halanx_admin.register(HouseOwnerTransaction, HouseOwnerTransactionAdmin)

