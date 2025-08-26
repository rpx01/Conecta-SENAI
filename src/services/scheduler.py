import atexit
import logging
import os
from typing import Optional

from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

try:  # pragma: no cover - fcntl may not be available on all platforms
    import fcntl  # type: ignore
except Exception:  # pragma: no cover - fallback when fcntl is absent
    fcntl = None  # type: ignore

from src.services.notificacao_service import (
    criar_notificacoes_agendamentos_proximos,
)

_scheduler: Optional[BackgroundScheduler] = None
_lock_file = None
_app: Optional[Flask] = None


def job_notificacoes_agendamentos() -> None:
    """Job de criação periódica de notificações."""
    global _app
    if _app is None:
        return
    with _app.app_context():
        criar_notificacoes_agendamentos_proximos()


def _shutdown_scheduler() -> None:
    global _scheduler, _lock_file
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
    if fcntl and _lock_file:
        try:
            fcntl.flock(_lock_file, fcntl.LOCK_UN)
        finally:
            _lock_file.close()
            _lock_file = None


def iniciar_scheduler(app) -> None:
    """Inicia o scheduler uma única vez por processo."""
    global _scheduler, _app, _lock_file

    if _scheduler is not None:
        logging.debug("Scheduler já iniciado; ignorando nova chamada")
        return

    if fcntl:
        try:
            _lock_file = open("/tmp/apscheduler.lock", "w")
            fcntl.flock(_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            logging.debug("Outra instância do scheduler já está em execução")
            _lock_file = None
            return
    else:
        logging.debug("fcntl não disponível; prosseguindo sem lock")

    _app = app
    intervalo = int(os.getenv("NOTIFICACAO_INTERVALO_MINUTOS", "60"))

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        job_notificacoes_agendamentos,
        "interval",
        minutes=intervalo,
        id="iniciar_scheduler_job",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

    _scheduler.start()
    atexit.register(_shutdown_scheduler)
    logging.info("Scheduler iniciado com intervalo de %s minutos", intervalo)
