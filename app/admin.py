from django.contrib import admin
from django.urls import path
from .models import Label
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
    list_display = ('barcode', 'stage', 'created_at', 'is_printed', 'printed_at')
    list_filter = ('stage', 'is_printed')
    search_fields = ('barcode', 'serial_number', 'imei_number', 'unique_number')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('barcode', 'stage', 'is_printed', 'printed_at')
        }),
        ('Second Stage Details', {
            'fields': ('serial_number', 'imei_number', 'unique_number'),
            'classes': ('collapse',),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.stage == 'first':
            return fieldsets[:1]  # Only show the first fieldset for first stage labels
        return fieldsets

# Replace the default admin site
admin.site = admin_site
