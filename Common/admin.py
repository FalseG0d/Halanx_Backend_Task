from django.contrib import admin

from Common.models import PaymentCategory
from Halanx.admin import halanxhomes_admin


class PaymentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_payment_category_icon_html')

    class Meta:
        model = PaymentCategory


halanxhomes_admin.register(PaymentCategory, PaymentCategoryAdmin)
