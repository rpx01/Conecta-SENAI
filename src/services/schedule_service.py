import datetime as dt

import pytz
import holidays
from flask import current_app

from src.models.treinamento import TurmaTreinamento

TZ = pytz.timezone("America/Sao_Paulo")
BR_HOL = holidays.country_holidays("BR", subdiv="MG")


def previous_business_day(d: dt.date) -> dt.date:
    """Retorna o dia útil anterior considerando fins de semana e feriados."""
    while d.weekday() >= 5 or d in BR_HOL:
        d -= dt.timedelta(days=1)
    return d


def convocacao_datetime(turma_inicio_date: dt.date) -> dt.datetime:
    d = previous_business_day(turma_inicio_date - dt.timedelta(days=1))
    return TZ.localize(dt.datetime(d.year, d.month, d.day, 12, 0, 0))


def schedule_convocacao_turma(turma: TurmaTreinamento, scheduler) -> None:
    """Agenda o envio de convocação para a turma informada."""
    run_dt = convocacao_datetime(turma.data_inicio)
    job_id = f"convocar_turma_{turma.id}_{turma.data_inicio:%Y%m%d}"

    def job():
        from src.services.convocacao_service import enviar_convocacao_turma

        with current_app.app_context():
            enviar_convocacao_turma(
                turma.id, force=False, origem="auto-scheduler"
            )

    now = dt.datetime.now(TZ)
    if run_dt <= now:
        # Se já passou mas o treinamento não começou, dispara imediatamente
        if turma.data_inicio >= now.date():
            job()
        return

    scheduler.add_job(
        job,
        "date",
        run_date=run_dt,
        id=job_id,
        replace_existing=True,
    )


def schedule_convocacoes_futuras(scheduler) -> None:
    """Agenda convocação para todas as turmas futuras ao iniciar o servidor."""
    hoje = dt.date.today()
    turmas = TurmaTreinamento.query.filter(
        TurmaTreinamento.data_inicio >= hoje
    ).all()
    for turma in turmas:
        schedule_convocacao_turma(turma, scheduler)
