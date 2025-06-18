import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class TemperatureConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'temptracker.temperature'

    def ready(self):
        """
        Método chamado quando a aplicação Django está pronta.
        Aqui inicializamos o scheduler.
        """
        try:
            # Importar aqui para evitar problemas de importação circular se scheduler for usado aqui
            from .models import scheduler 

            # Verificar se o scheduler já está rodando
            if not scheduler.running:
                scheduler.start()
                logger.info("Scheduler iniciado no AppConfig")

            # Recriar jobs existentes após reinicialização do servidor
            self._recreate_existing_jobs()

        except Exception as e:
            logger.error(f"Erro ao inicializar scheduler no AppConfig: {str(e)}")

    def _recreate_existing_jobs(self):
        """
        Recria os jobs para MonitorSettings ativos após reinicialização do servidor
        """
        try:
            # Mova estas importações para dentro da função
            from .models import MonitorSetting, scheduler 
            from apscheduler.triggers.interval import IntervalTrigger 

            # Buscar todas as configurações ativas
            active_monitors = MonitorSetting.objects.filter(is_active=True)

            for monitor in active_monitors:
                job_id = f"monitor_temp_{monitor.pk}"

                # Verificar se o job já existe
                try:
                    existing_job = scheduler.get_job(job_id)
                    if existing_job:
                        logger.info(f"Job {job_id} já existe, pulando...")
                        continue
                except:
                    pass  # Job não existe, vamos criar

                # Criar o job
                try:
                    scheduler.add_job(
                        func=monitor._monitor_temperature,
                        trigger=IntervalTrigger(minutes=monitor.monitoring_interval_minutes),
                        id=job_id,
                        name=f"Monitor {monitor.location_name}",
                        replace_existing=True,
                        max_instances=1
                    )
                    logger.info(f"Job recriado: {job_id} para {monitor.location_name}")

                except Exception as e:
                    logger.error(f"Erro ao recriar job {job_id}: {str(e)}")

        except Exception as e:
            logger.error(f"Erro ao recriar jobs existentes: {str(e)}")