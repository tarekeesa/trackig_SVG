# tracking_app/apps.py
from django.apps import AppConfig

class TrackingAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracking_app'
    verbose_name = 'Auto-Trigger Tracking'
