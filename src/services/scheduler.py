import logging
import os
from typing import Optional

from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

from src.services.notificacao_service import (
    criar_notificacoes_agendamentos_proximos,
)

scheduler = BackgroundScheduler()
_scheduler_started = False
_app: Optional[Flask] = None


def job_notificacoes_agendamentos() -> None:
    """Job de criação periódica de notificações."""
    global _app
    if _app is None:
        return
    with _app.app_context():
        criar_notificacoes_agendamentos_proximos()


def iniciar_scheduler(app) -> None:
    """Inicia o scheduler uma única vez por processo."""
    global _scheduler_started, _app

    if os.getenv("SCHEDULER_ENABLED", "1") in {"0", "false", "False"}:
        logging.info("Scheduler desabilitado via SCHEDULER_ENABLED=0")
        return

    if _scheduler_started:
        logging.debug("Scheduler já iniciado; ignorando nova chamada")
        return

    _app = app
    intervalo = int(os.getenv("NOTIFICACAO_INTERVALO_MINUTOS", "60"))

    scheduler.add_job(
        job_notificacoes_agendamentos,
        "interval",
        minutes=intervalo,
        id="notificacoes_agendamentos",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()
    _scheduler_started = True
    logging.info("Scheduler iniciado com intervalo de %s minutos", intervalo)
