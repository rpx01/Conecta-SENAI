"""Background scheduler setup."""

import os
from apscheduler.schedulers.background import BackgroundScheduler


scheduler = BackgroundScheduler()


def start_scheduler(app):
    """Start background scheduler if enabled."""
    intervalo = int(os.getenv("NOTIFICACAO_INTERVALO_MINUTOS", "60"))

    def job():
        from src.jobs.notificacoes import _executar_lembretes

        with app.app_context():
            _executar_lembretes()

    scheduler.add_job(
        job,
        "interval",
        minutes=intervalo,
        id="lembretes_notificacoes",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

    scheduler.start()
    with app.app_context():
        from src.services.schedule_service import schedule_convocacoes_futuras

        schedule_convocacoes_futuras(scheduler)
    return scheduler
