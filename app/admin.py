from django.contrib import admin
from django.urls import path
from .models import Label, ExcelData
from .dashboard import dashboard

class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(dashboard), name='admin_dashboard'),
        ]
        return custom_urls + urls

admin_site = CustomAdminSite(name='customadmin')

@admin.register(Label, site=admin_site)
class LabelAdmin(admin.ModelAdmin):
    list_display = ['barcode', 'stage', 'created_at']  # Removed is_printed and printed_at
    list_filter = ['stage']  # Removed is_printed
    search_fields = ['barcode', 'serial_number', 'imei_number']
    readonly_fields = ['created_at']

@admin.register(ExcelData)
class ExcelDataAdmin(admin.ModelAdmin):
    list_display = ['serial_number', 'imei_number', 'unique_number']
    search_fields = ['serial_number', 'imei_number', 'unique_number']

# Replace the default admin site
admin.site = admin_site
