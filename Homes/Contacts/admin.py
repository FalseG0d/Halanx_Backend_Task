from django.contrib import admin

from Halanx.admin import halanxhomes_admin
from Homes.Contacts.models import Enquiry


@admin.register(Enquiry, site=halanxhomes_admin)
class EnquiryModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'phone_no')

    class Meta:
        model = Enquiry
