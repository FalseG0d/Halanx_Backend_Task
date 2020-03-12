from django.contrib import admin

from Halanx.admin import halanxhomes_admin
from Homes.AreaManagers.models import AreaManager


@admin.register(AreaManager, site=halanxhomes_admin)
class AreaManagerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'area')
    raw_id_fields = ('user',)

