from django.contrib import admin

from .models import UptimeIP


@admin.register(UptimeIP)
class UptimeIPAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'current_status', 'is_active', 'check_interval_seconds', 'last_checked_at')
    list_filter = ('current_status', 'is_active')
    search_fields = ('name', 'url')
