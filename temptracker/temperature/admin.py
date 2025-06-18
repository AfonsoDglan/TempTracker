from django.contrib import admin
from .models import (TemperatureReading,
                     Alert,
                     MonitorSetting)


@admin.register(TemperatureReading)
class TemperatureReadingAdmin(admin.ModelAdmin):
    list_display = ('temperature_celsius',
                    'latitude',
                    'longitude',
                    'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('latitude', 'longitude')
    readonly_fields = ('timestamp',)


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('alert_temperature_celsius', 'alert_timestamp')
    list_filter = ('alert_timestamp',)
    search_fields = ('alert_temperature_celsius',)
    readonly_fields = ('alert_timestamp',)


@admin.register(MonitorSetting)
class MonitorSettingAdmin(admin.ModelAdmin):
    list_display = ('location_name',
                    'latitude',
                    'longitude',
                    'temperature_limit_celsius',
                    'monitoring_interval_minutes',
                    'notification_email',
                    'is_active',
                    'created_at')
    list_filter = ('is_active', 'monitoring_interval_minutes')
    search_fields = ('location_name',)
    readonly_fields = ('created_at', 'updated_at')
