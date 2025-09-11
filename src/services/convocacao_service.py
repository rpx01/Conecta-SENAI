from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Dict

from flask import current_app

from src.models import db
from src.models.treinamento import (
    InscricaoTreinamento,
    TurmaTreinamento,
)
from src.services.email_service import render_email_template, send_email

PLATAFORMA_URL = "https://mg.ead.senai.br/"
SENHA_INICIAL = "123456"


def build_convocacao_conteudo(turma, treinamento, inscricao):
    """Monta variáveis para o e-mail de convocação."""
    return {
        "teoria_online": bool(getattr(turma, "teoria_online", False)),
        "tem_pratica": bool(getattr(treinamento, "tem_pratica", False)),
        "local_realizacao": getattr(turma, "local_realizacao", "-") or "-",
        "usuario_login": getattr(inscricao, "email", ""),
        "senha_inicial": SENHA_INICIAL,
        "plataforma_url": PLATAFORMA_URL,
    }


@dataclass
class Result:
    ok: bool
    error: str | None = None


def enviar_convocacao_inscricao(
    inscricao: InscricaoTreinamento,
    turma: TurmaTreinamento,
    treinamento,
    origem: str,
) -> Result:
    if not inscricao.email:
        return Result(False, "Inscrição sem e-mail")

    fmt = "%d/%m/%Y"
    data_inicio = turma.data_inicio.strftime(fmt) if turma.data_inicio else "-"
    data_fim = turma.data_fim.strftime(fmt) if turma.data_fim else None
    ctx_extra = build_convocacao_conteudo(turma, treinamento, inscricao)

    html = render_email_template(
        "convocacao.html.j2",
        nome_inscrito=inscricao.nome,
        nome_treinamento=treinamento.nome,
        data_inicio=data_inicio,
        data_fim=data_fim,
        horario=turma.horario or "-",
        carga_horaria=(
            getattr(turma, "carga_horaria", None)
            or treinamento.carga_horaria
            or "-"
        ),
        instrutor=turma.instrutor.nome if turma.instrutor else "-",
        **ctx_extra,
    )

    subject = f"Convocação: {treinamento.nome} — {data_inicio}"
    try:
        send_email(to=inscricao.email, subject=subject, html=html)
        inscricao.convocado_em = dt.datetime.now(dt.timezone.utc)
        inscricao.convocado_por = origem
        db.session.commit()
        return Result(True)
    except Exception as exc:  # pragma: no cover - logging path
        db.session.rollback()
        current_app.logger.exception(
            "convocacao_inscricao_erro", extra={"inscricao_id": inscricao.id}
        )
        return Result(False, str(exc))


def enviar_convocacao_turma(
    turma_id: int, force: bool = False, origem: str = "manual"
) -> Dict[str, int]:
    turma = db.session.get(TurmaTreinamento, turma_id)
    if not turma:
        return {"enviados": 0, "pulados": 0, "falhas": 0}

    treinamento = turma.treinamento
    query = InscricaoTreinamento.query.filter_by(turma_id=turma_id)
    total = query.count()
    if not force:
        query = query.filter(InscricaoTreinamento.convocado_em.is_(None))
        pulados = total - query.count()
    else:
        pulados = 0

    enviados = 0
    falhas = 0
    for insc in query.all():
        res = enviar_convocacao_inscricao(insc, turma, treinamento, origem)
        if res.ok:
            enviados += 1
        else:
            falhas += 1
    return {"enviados": enviados, "pulados": pulados, "falhas": falhas}
