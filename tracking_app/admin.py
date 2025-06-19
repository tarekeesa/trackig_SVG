
# tracking_app/admin.py
from django.contrib import admin
from .models import AccessLog

@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'ip_address', 'trigger_type', 'trigger_method', 'via_ngrok']
    list_filter = ['trigger_type', 'trigger_method', 'via_ngrok', 'is_local_network', 'timestamp']
    search_fields = ['ip_address', 'hostname', 'mac_address', 'trigger_type']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('timestamp', 'ip_address', 'mac_address', 'hostname')
        }),
        ('Request Details', {
            'fields': ('request_path', 'query_params', 'user_agent', 'referer', 'headers')
        }),
        ('Tracking Info', {
            'fields': ('trigger_method', 'trigger_type', 'response_format', 'via_ngrok', 'is_local_network')
        }),
        ('Server Info', {
            'fields': ('server_mac', 'geolocation')
        }),
    )
