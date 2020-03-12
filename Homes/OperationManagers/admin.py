from django.contrib import admin

# Register your models here.
from Halanx.admin import halanxhomes_admin
from Homes.OperationManagers.models import OperationManager


@admin.register(OperationManager, site=halanxhomes_admin)
class OperationManagerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', )
    raw_id_fields = ('user', )
