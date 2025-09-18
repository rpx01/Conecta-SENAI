"""Rotinas de convocação automática de turmas."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from flask import current_app
from sqlalchemy.orm import joinedload

from src.models import db, InscricaoTreinamento, TurmaTreinamento
from src.services.email_service import EmailService


def _carregar_inscricoes_pendentes() -> Iterable[InscricaoTreinamento]:
    """Retorna as inscrições que ainda não receberam convocação."""

    return (
        InscricaoTreinamento.query.options(
            joinedload(InscricaoTreinamento.usuario),
            joinedload(InscricaoTreinamento.turma).joinedload(
                TurmaTreinamento.treinamento
            ),
            joinedload(InscricaoTreinamento.turma).joinedload(
                TurmaTreinamento.instrutor
            ),
        )
        .filter(InscricaoTreinamento.convocado_em.is_(None))
        .all()
    )


def _formatar_horario(turma: TurmaTreinamento) -> str:
    """Retorna representação textual do horário da turma."""

    hora_inicio = getattr(turma, "hora_inicio", None)
    hora_fim = getattr(turma, "hora_fim", None)
    if hora_inicio and hora_fim:
        return f"{hora_inicio} às {hora_fim}"

    if hora_inicio:
        return str(hora_inicio)

    horario = getattr(turma, "horario", None)
    return horario or "A definir"


def convocacao_automatica_job() -> None:
    """Executa a convocação automática de participantes."""

    logger = current_app.logger
    email_service = EmailService()

    inscricoes_a_convocar = _carregar_inscricoes_pendentes()
    if not inscricoes_a_convocar:
        logger.debug("Nenhuma inscrição pendente de convocação encontrada.")
        return

    for inscricao in inscricoes_a_convocar:
        turma = getattr(inscricao, "turma", None)
        treinamento = getattr(turma, "treinamento", None) if turma else None
        if turma is None or treinamento is None:
            logger.warning(
                "Inscrição %s sem turma ou treinamento associado; ignorando.",
                getattr(inscricao, "id", "?"),
            )
            continue

        aluno = getattr(inscricao, "usuario", None) or inscricao
        email_destino = (
            getattr(aluno, "email", None)
            or getattr(inscricao, "email", None)
        )
        if not email_destino:
            logger.warning(
                "Inscrição %s não possui e-mail cadastrado; convocação ignorada.",
                getattr(inscricao, "id", "?"),
            )
            continue

        contexto_email = {
            "nome": getattr(aluno, "name", None)
            or getattr(aluno, "nome", None)
            or getattr(inscricao, "nome", ""),
            "nome_treinamento": getattr(treinamento, "nome", ""),
            "data_inicio": turma.data_inicio.strftime("%d/%m/%Y")
            if getattr(turma, "data_inicio", None)
            else "",
            "data_fim": turma.data_fim.strftime("%d/%m/%Y")
            if getattr(turma, "data_fim", None)
            else "",
            "horario": _formatar_horario(turma),
            "local": getattr(turma, "local", None)
            or getattr(turma, "local_realizacao", None)
            or "A definir",
            "instrutor": getattr(getattr(turma, "instrutor", None), "nome", None)
            or "A definir",
        }

        try:
            email_service.send_email(
                to=email_destino,
                subject=(
                    f"CONVOCAÇÃO PARA O TREINAMENTO: "
                    f"{contexto_email['nome_treinamento']}"
                ),
                template="email/convocacao.html.j2",
                **contexto_email,
            )
        except Exception:  # pragma: no cover - apenas log
            logger.exception(
                "Falha ao enviar convocação automática para inscrição %s.",
                getattr(inscricao, "id", "?"),
            )
            continue

        inscricao.convocado_em = datetime.utcnow()

    try:
        db.session.commit()
    except Exception:  # pragma: no cover - apenas log
        db.session.rollback()
        logger.exception(
            "Erro ao salvar o status das convocações automáticas no banco de dados.",
        )
        raise
