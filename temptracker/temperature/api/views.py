from rest_framework import generics
from temperature.models import (TemperatureReading,
                                Alert,
                                MonitorSetting)
from temperature.api.serializers import (MonitorSettingSerializer,
                                         TemperatureReadingSerializer,
                                         AlertSerializer)
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView


class MonitorSettingListCreateAPIView(generics.ListCreateAPIView):
    """
    API View para listar e criar configurações de monitoramento.
    - GET: Lista todas as configurações existentes.
    - POST: Cria uma nova configuração de monitoramento.
    """
    queryset = MonitorSetting.objects.all()
    serializer_class = MonitorSettingSerializer


class TemperatureReadingListAPIView(generics.ListAPIView):
    """
    API View para listar leituras de temperatura com filtro de período e ID da localidade.
    - GET:
      - Retorna as leituras das últimas 24 horas e de todas as localidades por padrão.
      - Pode receber um parâmetro 'time_range' na URL para filtrar por período:
        - '24h': Últimas 24 horas.
        - '7d': Últimos 7 dias.
        - '30d': Últimos 30 dias.
      - Pode receber um parâmetro 'location_id' na URL para filtrar por ID da localidade (ex: 1, 2).
    """
    serializer_class = TemperatureReadingSerializer

    def get_queryset(self):
        """
        Retorna leituras de temperatura filtradas por período e/ou ID da localidade.
        """
        time_range = self.request.query_params.get('time_range', '24h')

        end_time = timezone.now()
        start_time = None

        if time_range == '24h':
            start_time = end_time - timedelta(hours=24)
        elif time_range == '7d':
            start_time = end_time - timedelta(days=7)
        elif time_range == '30d':
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(hours=24)

        queryset = TemperatureReading.objects.filter(timestamp__gte=start_time)

        location_id_param = self.request.query_params.get('location_id')

        if location_id_param:
            try:
                location_id = int(location_id_param)
                queryset = queryset.filter(monitor_setting__id=location_id)
            except ValueError:
                raise ValidationError({"location_id": "O ID da localidade deve ser um número inteiro válido."})

        queryset = queryset.order_by('-timestamp')
        return queryset


class AlertListCreateAPIView(generics.ListAPIView):
    """
    API View para listar os alertas.
    - GET: Lista todos os alertas existentes.
    """
    queryset = Alert.objects.filter(read_confirmation=False).order_by('-alert_timestamp')
    serializer_class = AlertSerializer


class AlertConfirmView(APIView):
    """
    API View para confirmar a leitura de um alerta usando requisição POST.
    - POST: Define 'read_confirmation' para True para o alerta especificado pelo ID.
    """
    def post(self, request, pk, format=None):
        alert = get_object_or_404(Alert, pk=pk)

        if alert.read_confirmation:
            serializer = AlertSerializer(alert) 
            return Response(
                {"detail": "Alerta já confirmado.", "alert": serializer.data},
                status=status.HTTP_200_OK
            )
        alert.read_confirmation = True
        alert.save(update_fields=['read_confirmation'])

        serializer = AlertSerializer(alert)
        return Response(serializer.data, status=status.HTTP_200_OK)
