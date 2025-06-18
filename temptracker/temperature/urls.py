from django.urls import path
from . import views
from temperature.api.views import (MonitorSettingListCreateAPIView,
                                   TemperatureReadingListAPIView,
                                   AlertListCreateAPIView,
                                   AlertConfirmView,)

urlpatterns = [
    path('', views.monitor_status, name='monitor_status'),
    path('api/v1/monitor-settings/', MonitorSettingListCreateAPIView.as_view(), name='monitor_settings'),
    path('api/v1/temperature-readings/', TemperatureReadingListAPIView.as_view(), name='temperature_readings'),
    path('api/v1/alerts/', AlertListCreateAPIView.as_view(), name='alerts'),
    path('api/v1/alerts/confirm/<int:pk>/', AlertConfirmView.as_view(), name="api_alert_confirm"),
]
