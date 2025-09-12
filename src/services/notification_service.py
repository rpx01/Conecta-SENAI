"""Email notifications for Turma events."""
from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Dict, List

from flask import current_app

from src.models import (
    db,
    SecretariaTreinamentos,
    TurmaTreinamento,
    Instrutor,
)
from .email_service import send_email

logger = logging.getLogger(__name__)
TZ = ZoneInfo("America/Sao_Paulo")
FMT_DATE = "%d/%m/%Y"
FMT_DATETIME = "%d/%m/%Y %H:%M"


def _format_date(value: datetime | None) -> str:
    if not value:
        return "-"
    if isinstance(value, datetime):
        return value.astimezone(TZ).strftime(FMT_DATE)
    return value.strftime(FMT_DATE)


def _format_bool(val: Any) -> str:
    return "Sim" if val else "Não"


def _render(template: str, **ctx: Any) -> str:
    template_obj = current_app.jinja_env.get_or_select_template(f"emails/{template}")
    return template_obj.render(**ctx)


def get_secretaria_recipients() -> List[str]:
    registros = SecretariaTreinamentos.query.filter_by(ativo=True).all()
    return [r.email for r in registros if r.email]


def build_turma_snapshot(turma: TurmaTreinamento) -> Dict[str, Any]:
    return {
        "id": turma.id,
        "treinamento_id": turma.treinamento_id,
        "treinamento_nome": getattr(turma.treinamento, "nome", ""),
        "instrutor_id": turma.instrutor_id,
        "instrutor_nome": getattr(turma.instrutor, "nome", None),
        "data_inicio": turma.data_inicio,
        "data_fim": turma.data_fim,
        "horario": getattr(turma, "horario", None),
        "local_realizacao": getattr(turma, "local_realizacao", None),
        "carga_horaria": getattr(turma, "carga_horaria", None),
        "teoria_online": getattr(turma, "teoria_online", None),
        "link_teoria": getattr(turma, "link_teoria", None),
        "observacoes": getattr(turma, "observacoes", None),
    }


_FIELDS_MAP = {
    "instrutor_id": "Instrutor",
    "data_inicio": "Data Início",
    "data_fim": "Data Fim",
    "horario": "Horário",
    "local_realizacao": "Local",
    "carga_horaria": "Carga horária",
    "teoria_online": "Teoria online",
    "link_teoria": "Link teoria",
    "observacoes": "Observações",
}


def _humanize(field: str, value: Any, snapshot: Dict[str, Any]) -> str:
    if value is None:
        return "-"
    if field in ("data_inicio", "data_fim"):
        return _format_date(value)
    if field == "teoria_online":
        return _format_bool(value)
    if field == "instrutor_id":
        return snapshot.get("instrutor_nome") or "-"
    return str(value)


def build_turma_diff(old: Dict[str, Any], new: Dict[str, Any]) -> List[Dict[str, str]]:
    diffs: List[Dict[str, str]] = []
    for field, label in _FIELDS_MAP.items():
        if old.get(field) != new.get(field):
            diffs.append(
                {
                    "campo": label,
                    "de": _humanize(field, old.get(field), old),
                    "para": _humanize(field, new.get(field), new),
                }
            )
    return diffs


def _format_snapshot(snap: Dict[str, Any]) -> Dict[str, Any]:
    snap = snap.copy()
    snap["data_inicio_fmt"] = _format_date(snap.get("data_inicio"))
    snap["data_fim_fmt"] = _format_date(snap.get("data_fim"))
    snap["teoria_online_fmt"] = _format_bool(snap.get("teoria_online"))
    return snap


def send_new_turma_notifications(turma_id: int) -> None:
    turma = db.session.get(TurmaTreinamento, turma_id)
    if not turma:
        return
    snap = _format_snapshot(build_turma_snapshot(turma))
    subject_secretaria = f"[Treinamentos] Nova Turma #{turma.id} – {snap['treinamento_nome']}"
    subject_instrutor = f"[Treinamentos] Você foi designado para a Turma #{turma.id} – {snap['treinamento_nome']}"

    # E-mail para instrutor
    instrutor_email = getattr(turma.instrutor, "email", None)
    if instrutor_email:
        try:
            html = _render("turma_criada_instrutor.html", turma=snap, instrutor=turma.instrutor)
            send_email(to=instrutor_email, subject=subject_instrutor, html=html)
        except Exception as exc:  # pragma: no cover - apenas log
            logger.error("Falha ao enviar e-mail para instrutor: %s", exc)
    else:
        logger.warning("Instrutor sem e-mail para turma %s", turma.id)

    # E-mail para secretaria
    try:
        html = _render("turma_criada_secretaria.html", turma=snap)
        recipients = get_secretaria_recipients()
        if recipients:
            send_email(to=recipients, subject=subject_secretaria, html=html)
    except Exception as exc:  # pragma: no cover - apenas log
        logger.error("Falha ao notificar secretaria sobre nova turma: %s", exc)


def send_turma_update_notifications(turma_before: Dict[str, Any], turma_after_id: int) -> None:
    turma = db.session.get(TurmaTreinamento, turma_after_id)
    if not turma:
        return
    after = build_turma_snapshot(turma)
    diffs = build_turma_diff(turma_before, after)
    snap = _format_snapshot(after)

    if diffs:
        try:
            html = _render(
                "turma_atualizada_secretaria.html",
                turma=snap,
                diffs=diffs,
            )
            recipients = get_secretaria_recipients()
            if recipients:
                subject = f"[Treinamentos] Atualização na Turma #{turma.id} – {snap['treinamento_nome']}"
                send_email(to=recipients, subject=subject, html=html)
        except Exception as exc:  # pragma: no cover
            logger.error("Falha ao enviar diff para secretaria: %s", exc)

    if turma_before.get("instrutor_id") != after.get("instrutor_id"):
        old_id = turma_before.get("instrutor_id")
        new_id = after.get("instrutor_id")
        if old_id and old_id != new_id:
            antigo = db.session.get(Instrutor, old_id)
            if antigo and antigo.email:
                try:
                    html = _render(
                        "turma_instrutor_removido.html",
                        turma=snap,
                        instrutor=antigo,
                    )
                    subject = f"[Treinamentos] Atualização: você não ministrará mais a Turma #{turma.id} – {snap['treinamento_nome']}"
                    send_email(to=antigo.email, subject=subject, html=html)
                except Exception as exc:  # pragma: no cover
                    logger.error("Erro ao notificar instrutor removido: %s", exc)
        if new_id and new_id != old_id:
            novo = turma.instrutor or db.session.get(Instrutor, new_id)
            if novo and novo.email:
                try:
                    html = _render(
                        "turma_instrutor_designado.html",
                        turma=snap,
                        instrutor=novo,
                    )
                    subject = f"[Treinamentos] Você foi designado para a Turma #{turma.id} – {snap['treinamento_nome']}"
                    send_email(to=novo.email, subject=subject, html=html)
                except Exception as exc:  # pragma: no cover
                    logger.error("Erro ao notificar novo instrutor: %s", exc)
