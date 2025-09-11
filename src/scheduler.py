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

    def convocacao_job():
        from src.jobs.convocacao_automatica import convocacao_automatica_job

        with app.app_context():
            convocacao_automatica_job()

    scheduler.add_job(
        convocacao_job,
        "interval",
        hours=1,
        id="convocacao_automatica",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

    scheduler.start()
    return scheduler
