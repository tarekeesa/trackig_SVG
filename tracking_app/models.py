
# tracking_app/models.py
from django.db import models
from django.utils import timezone
import json

class AccessLog(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField()
    mac_address = models.CharField(max_length=17, blank=True, null=True)
    hostname = models.CharField(max_length=255, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    referer = models.URLField(blank=True, null=True)
    request_path = models.CharField(max_length=500)
    query_params = models.JSONField(default=dict)
    server_mac = models.CharField(max_length=17, blank=True, null=True)
    geolocation = models.JSONField(default=dict)
    trigger_method = models.CharField(max_length=100, blank=True, null=True)
    trigger_type = models.CharField(max_length=100, blank=True, null=True)
    headers = models.JSONField(default=dict)
    is_local_network = models.BooleanField(default=False)
    via_ngrok = models.BooleanField(default=False)
    response_format = models.CharField(max_length=20, default='json')
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['trigger_type']),
            models.Index(fields=['trigger_method']),
        ]
    
    def __str__(self):
        return f"{self.timestamp} - {self.ip_address} - {self.trigger_type}"
    
    @property
    def trigger_category(self):
        """Determine trigger category based on trigger type"""
        trigger_type = self.trigger_type or ''
        
        if 'js_' in trigger_type or 'rapid_fire' in trigger_type:
            return "🚀 JAVASCRIPT AUTO-TRIGGER"
        elif 'grid_' in trigger_type:
            return "🕸️ INVISIBLE GRID TRIGGER"
        elif 'overlay_' in trigger_type:
            return "🎭 OVERLAY TRIGGER"
        elif 'micro_' in trigger_type:
            return "🎯 MICRO-PIXEL TRIGGER"
        elif 'strategic_' in trigger_type:
            return "📍 STRATEGIC AREA TRIGGER"
        elif 'svg_' in trigger_type:
            return "🖼️ SVG INJECTION TRIGGER"
        elif 'html_' in trigger_type:
            return "📄 HTML AUTO-TRIGGER"
        else:
            return "⚡ AUTO-TRIGGER"
