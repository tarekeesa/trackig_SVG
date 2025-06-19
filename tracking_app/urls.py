# tracking_app/urls.py - Updated with map view
from django.urls import path
from . import views

app_name = 'tracking_app'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('track/', views.track_endpoint, name='track'),
    path('status/', views.status_dashboard, name='status'),
    path('map/', views.map_view, name='map'),  # New map view
    path('logs/', views.logs_api, name='logs'),
    path('api/logs/', views.logs_api, name='api_logs'),
]
