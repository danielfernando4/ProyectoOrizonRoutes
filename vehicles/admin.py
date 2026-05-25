from django.contrib import admin

from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'capacity', 'owner')
    list_filter = ('brand',)
    search_fields = ('brand', 'model', 'owner__username')
