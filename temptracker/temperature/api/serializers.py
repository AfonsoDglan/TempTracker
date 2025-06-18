from rest_framework import serializers
from ..models import MonitorSetting, TemperatureReading, Alert


class MonitorSettingSerializer(serializers.ModelSerializer):
    """
    Serializador para o modelo MonitorSetting.
    Permite criar e listar configurações de monitoramento.
    """
    class Meta:
        model = MonitorSetting
        fields = '__all__' # Inclui todos os campos do modelo
        read_only_fields = ('created_at', 'updated_at') # Campos que não podem ser definidos na criação/atualização


class TemperatureReadingSerializer(serializers.ModelSerializer):
    """
    Serializador para o modelo TemperatureReading.
    Permite listar leituras de temperatura.
    Inclui o nome da localidade do MonitorSetting associado para melhor contexto.
    """
    location_name = serializers.CharField(source='monitor_setting.location_name', read_only=True)

    class Meta:
        model = TemperatureReading
        # Excluímos 'latitude' e 'longitude' aqui, pois já vêm do monitor_setting
        # Se quiser mantê-los para redundância ou outros propósitos, adicione-os de volta.
        fields = ['id', 'location_name', 'temperature_celsius', 'timestamp', 'generated_notification']
        read_only_fields = ('timestamp',) # timestamp é definido automaticamente


class AlertSerializer(serializers.ModelSerializer):
    """
    Serializador para o modelo Alert.
    Permite criar e listar alertas.
    Inclui o nome da localidade do MonitorSetting associado para melhor contexto.
    """
    location_name = serializers.CharField(source='monitor_setting.location_name', read_only=True)

    class Meta:
        model = Alert
        fields = '__all__' # Inclui todos os campos do modelo
        read_only_fields = ('alert_timestamp',) # alert_timestamp é definido automaticamente
