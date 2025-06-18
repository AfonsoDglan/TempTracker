from django.db import models
from django_apscheduler.jobstores import DjangoJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import requests
import logging
from .email import send_email_alert


logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")


class MonitorSetting(models.Model):
    """
    Define as configurações para o monitoramento de temperatura de uma localidade.
    """
    location_name = models.CharField(
        max_length=255,
        verbose_name="Nome da Localidade",
        help_text="Nome da localidade a ser monitorada."
    )
    latitude = models.FloatField(
        verbose_name="Latitude",
        help_text="Latitude da localidade para monitoramento."
    )
    longitude = models.FloatField(
        verbose_name="Longitude",
        help_text="Longitude da localidade para monitoramento."
    )
    temperature_limit_celsius = models.FloatField(
        verbose_name="Limite de Temperatura (°C)",
        help_text="Temperatura em Celsius que, se excedida, dispara um alerta."
    )
    monitoring_interval_minutes = models.IntegerField(
        verbose_name="Intervalo de Monitoramento (minutos)",
        help_text="Frequência (em minutos) com que a temperatura será verificada."
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativar Monitoramento",
        help_text="Se selecionado, o monitoramento para esta localidade será ativado automaticamente."
    )
    notification_email = models.EmailField(
        blank=False,
        null=False,
        default="teste@gmail.com",
        verbose_name="Email de Notificação",
        help_text="Endereço de e-mail para enviar alertas de temperatura."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )

    class Meta:
        verbose_name = "Configuração de Monitoramento"
        verbose_name_plural = "Configurações de Monitoramento"
        ordering = ['location_name']

    def __str__(self):
        return f"Monitorando {self.location_name} (Limite: {self.temperature_limit_celsius}°C, Intervalo: {self.monitoring_interval_minutes}min)"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_instance = None

        if not is_new:
            try:
                old_instance = MonitorSetting.objects.get(pk=self.pk)
            except MonitorSetting.DoesNotExist:
                is_new = True

        super().save(*args, **kwargs)

        job_id = f"monitor_temp_{self.pk}"

        try:
            if not is_new and old_instance:
                try:
                    scheduler.remove_job(job_id)
                    logger.info(f"Job removido: {job_id}")
                except Exception as e:
                    logger.error(f"Erro ao remover o job {job_id}: {e}")

            if self.is_active:
                scheduler.add_job(
                    func=self._monitor_temperature,
                    trigger=IntervalTrigger(minutes=self.monitoring_interval_minutes),
                    id=job_id,
                    name=f"Monitor {self.location_name}",
                    replace_existing=True,
                    max_instances=1
                )
                logger.info(f"Monitoramento iniciado para {self.location_name} - Job ID: {job_id}")
            else:
                logger.info(f"Monitoramento desativado para {self.location_name}")

        except Exception as e:
            logger.error(f"Erro ao configurar monitoramento para {self.location_name}: {str(e)}")

        if not scheduler.running:
            scheduler.start()
            logger.info("Scheduler iniciado com sucesso.")

    def delete(self, *args, **kwargs):
        """Remove o job do scheduler quando o MonitorSetting é deletado"""
        job_id = f"monitor_temp_{self.pk}"
        try:
            scheduler.remove_job(job_id)
            logger.info(f"Job removido na exclusão: {job_id}")
        except Exception as e:
            logger.warning(f"Falha ao remover o job: {e}")
        logger.info(f"MonitorSetting {self.pk} deletado com sucesso.")
        super().delete(*args, **kwargs)

    def _monitor_temperature(self):
        """
        Método que será executado pelo scheduler para monitorar a temperatura
        """
        try:
            temperature = self._get_current_temperature()
            reading = TemperatureReading.objects.create(
                monitor_setting=self,
                temperature_celsius=temperature,
                latitude=self.latitude,
                longitude=self.longitude
            )

            logger.info(f"Leitura registrada: {reading}")

            if temperature > self.temperature_limit_celsius:
                alert = Alert.objects.create(
                    monitor_setting=self,
                    alert_temperature_celsius=temperature
                )
                logger.warning(f"ALERTA CRIADO: {alert}")
                reading.generated_notification = True
                reading.save()
                alert.notify()
        except Exception as e:
            logger.error(f"Erro no monitoramento de {self.location_name}: {str(e)}")

    def _get_current_temperature(self):
        """
        Método para obter a temperatura atual da localidade usando Open-Meteo API
        """
        try:
            url = "https://api.open-meteo.com/v1/forecast"

            params = {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'current': 'temperature_2m',
                'timezone': 'auto',
                'forecast_days': 1
            }

            logger.info(f"Fazendo requisição para Open-Meteo API - {self.location_name} ({self.latitude}, {self.longitude})")

            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()  # Levanta exceção para códigos de erro HTTP

            data = response.json()

            if 'current' in data and 'temperature_2m' in data['current']:
                temperature = data['current']['temperature_2m']

                if temperature is not None and isinstance(temperature, (int, float)):
                    temperature = round(float(temperature), 2)

                    logger.info(f"Temperatura obtida com sucesso para {self.location_name}: {temperature}°C")
                    return temperature
                else:
                    raise ValueError("Temperatura retornada é inválida")
            else:
                raise ValueError("Dados de temperatura não encontrados na resposta da API")

        except requests.exceptions.Timeout:
            logger.error(f"Timeout ao obter temperatura para {self.location_name}")
            raise Exception("Timeout na requisição à API de clima")

        except requests.exceptions.ConnectionError:
            logger.error(f"Erro de conexão ao obter temperatura para {self.location_name}")
            raise Exception("Erro de conexão com a API de clima")

        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP ao obter temperatura para {self.location_name}: {e}")
            raise Exception(f"Erro HTTP na API de clima: {e}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {self.location_name}: {e}")
            raise Exception(f"Erro na requisição à API de clima: {e}")

        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Erro ao processar dados da API para {self.location_name}: {e}")
            raise Exception(f"Erro ao processar dados da API: {e}")

        except Exception as e:
            logger.error(f"Erro inesperado ao obter temperatura para {self.location_name}: {str(e)}")
            raise

    def stop_monitoring(self):
        """Método para parar o monitoramento manualmente"""
        job_id = f"monitor_temp_{self.pk}"
        try:
            scheduler.remove_job(job_id)
            logger.info(f"Monitoramento parado para {self.location_name}")
        except:
            logger.warning(f"Job {job_id} não encontrado para parar")

    def restart_monitoring(self):
        """Método para reiniciar o monitoramento"""
        if self.is_active:
            self.stop_monitoring()
            job_id = f"monitor_temp_{self.pk}"
            scheduler.add_job(
                func=self._monitor_temperature,
                trigger=IntervalTrigger(minutes=self.monitoring_interval_minutes),
                id=job_id,
                name=f"Monitor {self.location_name}",
                replace_existing=True,
                max_instances=1
            )
            logger.info(f"Monitoramento reiniciado para {self.location_name}")


class TemperatureReading(models.Model):
    """
    Representa uma leitura de temperatura de uma localidade em um determinado momento.
    Agora inclui uma chave estrangeira para a configuração do monitoramento.
    """
    monitor_setting = models.ForeignKey(
        MonitorSetting,
        on_delete=models.CASCADE,
        related_name='temperature_readings',
        verbose_name="Configuração do Monitor",
        help_text="Configuração de monitoramento à qual esta leitura pertence."
    )
    temperature_celsius = models.FloatField(
        verbose_name="Temperatura (°C)",
        help_text="Temperatura em graus Celsius."
    )
    latitude = models.FloatField(
        verbose_name="Latitude",
        help_text="Latitude da localidade da leitura."
    )
    longitude = models.FloatField(
        verbose_name="Longitude",
        help_text="Longitude da localidade da leitura."
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data/Hora da Leitura",
        help_text="Data e hora em que a leitura foi registrada."
    )
    generated_notification = models.BooleanField(
        default=False,
        verbose_name="Confirmação de geração de alerta",
        help_text="Indica se foi criado um alerta."
    )

    class Meta:
        verbose_name = "Leitura de Temperatura"
        verbose_name_plural = "Leituras de Temperatura"
        ordering = ['-timestamp']

    def __str__(self):
        return f"Leitura de {self.monitor_setting.location_name} - {self.temperature_celsius}°C at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class Alert(models.Model):
    """
    Representa um alerta disparado quando a temperatura excede um limite.
    """
    alert_temperature_celsius = models.FloatField(
        verbose_name="Temperatura do Alerta (°C)",
        help_text="Temperatura que disparou o alerta."
    )
    alert_timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data/Hora do Alerta",
        help_text="Data e hora em que o alerta foi disparado."
    )
    monitor_setting = models.ForeignKey(
        MonitorSetting,
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name="Configuração do Monitor",
        help_text="Configuração de monitoramento que gerou este alerta."
    )
    read_confirmation = models.BooleanField(
        default=False,
        verbose_name="Confirmação de Leitura",
        help_text="Indica se o alerta foi visualizado/confirmado."
    )
    notification_sent = models.BooleanField(
        default=False,
        verbose_name="Notificação Enviada",
        help_text="Indica se uma notificação sobre este alerta foi enviada."
    )

    class Meta:
        verbose_name = "Alerta de Temperatura"
        verbose_name_plural = "Alertas de Temperatura"
        ordering = ['-alert_timestamp']

    def __str__(self):
        return f"ALERTA para {self.monitor_setting.location_name}: {self.alert_temperature_celsius}°C excedeu o limite em {self.alert_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    def notify(self):
        if not self.notification_sent:
            try:
                send_email_alert(
                    self.monitor_setting.location_name,
                    self.alert_temperature_celsius,
                    self.alert_timestamp,
                    self.monitor_setting.notification_email,
                    self.id,
                    self.monitor_setting.temperature_limit_celsius)
                self.notification_sent = True
                self.save()
                logger.info(f"Notification sent for alert ID {self.id}")
            except Exception as e:
                logger.error(f"Failed to send notification for alert ID {self.id}: {e}")
