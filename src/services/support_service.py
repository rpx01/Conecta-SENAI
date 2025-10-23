"""Serviços de negócio para o módulo de suporte de TI."""

from __future__ import annotations

import logging
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Sequence
from uuid import uuid4

from flask import current_app
from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from src.models import db
from src.models.support import (
    SupportArea,
    SupportEquipmentType,
    SupportTicket,
    SupportTicketAttachment,
)
from src.schemas.support import (
    SupportKnowledgeBaseSchema,
    SupportTicketCreateSchema,
    SupportTicketUpdateSchema,
)
from src.utils.support_constants import VALID_STATUSES, VALID_URGENCIAS

log = logging.getLogger(__name__)

UPLOAD_SUBDIR = Path("uploads") / "suporte-ti"
MAX_ANEXOS = 5
URGENCIA_PRIORIDADE = {valor: idx for idx, valor in enumerate(VALID_URGENCIAS, start=1)}


class SupportServiceError(Exception):
    """Erro genérico do módulo de suporte."""


def _obter_pasta_upload() -> Path:
    pasta_base = Path(current_app.static_folder)
    destino = pasta_base / UPLOAD_SUBDIR
    destino.mkdir(parents=True, exist_ok=True)
    return destino


def _gerar_nome_arquivo(nome_original: str | None) -> str:
    seguro = secure_filename(nome_original or "")
    extensao = Path(seguro).suffix
    if not extensao:
        extensao = mimetypes.guess_extension("image/jpeg") or ".jpg"
    return f"{uuid4().hex}{extensao}"


def _salvar_anexo(arquivo: FileStorage) -> dict:
    if not arquivo or not arquivo.filename:
        raise SupportServiceError("Arquivo de anexo inválido")

    mimetype = (arquivo.mimetype or "").lower()
    if not mimetype.startswith("image/"):
        raise SupportServiceError("Somente arquivos de imagem são permitidos nos anexos")

    pasta = _obter_pasta_upload()
    nome_arquivo = _gerar_nome_arquivo(arquivo.filename)
    caminho_absoluto = pasta / nome_arquivo
    arquivo.stream.seek(0)
    conteudo = arquivo.read()
    arquivo.stream.seek(0)
    caminho_absoluto.write_bytes(conteudo)

    caminho_relativo = (UPLOAD_SUBDIR / nome_arquivo).as_posix()
    return {
        "nome_arquivo": nome_arquivo,
        "caminho_relativo": caminho_relativo,
        "content_type": mimetype,
    }


def _carregar_lookup(modelo: type[SupportArea] | type[SupportEquipmentType], apenas_ativos: bool | None) -> list:
    consulta = modelo.query
    if apenas_ativos is True:
        consulta = consulta.filter_by(ativo=True)
    elif apenas_ativos is False:
        consulta = consulta.filter_by(ativo=False)
    return consulta.order_by(modelo.nome.asc()).all()


def listar_areas(apenas_ativas: bool | None = True) -> list[SupportArea]:
    return _carregar_lookup(SupportArea, apenas_ativas)


def listar_tipos_equipamento(apenas_ativos: bool | None = True) -> list[SupportEquipmentType]:
    return _carregar_lookup(SupportEquipmentType, apenas_ativos)


def criar_area(dados: SupportKnowledgeBaseSchema) -> SupportArea:
    area = SupportArea(nome=dados.nome, descricao=dados.descricao, ativo=dados.ativo)
    try:
        db.session.add(area)
        db.session.commit()
    except IntegrityError as exc:  # pragma: no cover - comportamento específico de banco
        db.session.rollback()
        log.warning("Falha ao criar área de suporte: %s", exc)
        raise SupportServiceError("Já existe uma área cadastrada com esse nome") from exc
    return area


def atualizar_area(area_id: int, dados: SupportKnowledgeBaseSchema) -> SupportArea:
    area = db.session.get(SupportArea, area_id)
    if not area:
        raise SupportServiceError("Área não encontrada")
    area.nome = dados.nome
    area.descricao = dados.descricao
    area.ativo = dados.ativo
    try:
        db.session.commit()
    except IntegrityError as exc:  # pragma: no cover
        db.session.rollback()
        raise SupportServiceError("Já existe uma área cadastrada com esse nome") from exc
    return area


def remover_area(area_id: int) -> None:
    area = db.session.get(SupportArea, area_id)
    if not area:
        raise SupportServiceError("Área não encontrada")
    try:
        db.session.delete(area)
        db.session.commit()
    except SQLAlchemyError as exc:  # pragma: no cover
        db.session.rollback()
        raise SupportServiceError("Não foi possível remover a área") from exc


def criar_tipo_equipamento(dados: SupportKnowledgeBaseSchema) -> SupportEquipmentType:
    equipamento = SupportEquipmentType(
        nome=dados.nome, descricao=dados.descricao, ativo=dados.ativo
    )
    try:
        db.session.add(equipamento)
        db.session.commit()
    except IntegrityError as exc:  # pragma: no cover
        db.session.rollback()
        log.warning("Falha ao criar tipo de equipamento: %s", exc)
        raise SupportServiceError("Já existe um tipo de equipamento com esse nome") from exc
    return equipamento


def atualizar_tipo_equipamento(
    equipamento_id: int, dados: SupportKnowledgeBaseSchema
) -> SupportEquipmentType:
    equipamento = db.session.get(SupportEquipmentType, equipamento_id)
    if not equipamento:
        raise SupportServiceError("Tipo de equipamento não encontrado")
    equipamento.nome = dados.nome
    equipamento.descricao = dados.descricao
    equipamento.ativo = dados.ativo
    try:
        db.session.commit()
    except IntegrityError as exc:  # pragma: no cover
        db.session.rollback()
        raise SupportServiceError("Já existe um tipo de equipamento com esse nome") from exc
    return equipamento


def remover_tipo_equipamento(equipamento_id: int) -> None:
    equipamento = db.session.get(SupportEquipmentType, equipamento_id)
    if not equipamento:
        raise SupportServiceError("Tipo de equipamento não encontrado")
    try:
        db.session.delete(equipamento)
        db.session.commit()
    except SQLAlchemyError as exc:  # pragma: no cover
        db.session.rollback()
        raise SupportServiceError("Não foi possível remover o tipo de equipamento") from exc


def _validar_lookup_ids(area_id: int | None, equipamento_id: int | None) -> None:
    if area_id:
        area = db.session.get(SupportArea, area_id)
        if not area or not area.ativo:
            raise SupportServiceError("Área selecionada inválida")
    if equipamento_id:
        equipamento = db.session.get(SupportEquipmentType, equipamento_id)
        if not equipamento or not equipamento.ativo:
            raise SupportServiceError("Tipo de equipamento inválido")


def criar_chamado(
    usuario_id: int,
    dados: SupportTicketCreateSchema,
    anexos: Sequence[FileStorage],
) -> SupportTicket:
    if anexos and len([a for a in anexos if a and a.filename]) > MAX_ANEXOS:
        raise SupportServiceError("É permitido anexar no máximo 5 arquivos")

    _validar_lookup_ids(dados.area_id, dados.equipamento_id)

    ticket = SupportTicket(
        usuario_id=usuario_id,
        nome=dados.nome,
        email=dados.email,
        area_id=dados.area_id,
        equipamento_id=dados.equipamento_id,
        patrimonio=dados.patrimonio,
        numero_serie=dados.numero_serie,
        descricao=dados.descricao,
        urgencia=dados.urgencia,
        status="aberto",
    )

    anexos_salvos: list[dict] = []
    for arquivo in anexos or []:
        if not arquivo or not arquivo.filename:
            continue
        anexos_salvos.append(_salvar_anexo(arquivo))

    try:
        db.session.add(ticket)
        db.session.flush()
        for anexo in anexos_salvos:
            attachment = SupportTicketAttachment(ticket_id=ticket.id, **anexo)
            db.session.add(attachment)
        db.session.commit()
    except SupportServiceError:
        raise
    except Exception as exc:  # pragma: no cover - rollback defensivo
        db.session.rollback()
        log.exception("Erro ao criar chamado de suporte")
        raise SupportServiceError("Não foi possível registrar o chamado") from exc

    return ticket


def _serializar_anexo(anexo: SupportTicketAttachment) -> dict:
    return {
        "id": anexo.id,
        "nome_arquivo": anexo.nome_arquivo,
        "url": anexo.url_publica(),
        "content_type": anexo.content_type,
    }


def serializar_chamado(ticket: SupportTicket) -> dict:
    return {
        "id": ticket.id,
        "usuario_id": ticket.usuario_id,
        "nome": ticket.nome,
        "email": ticket.email,
        "area_id": ticket.area_id,
        "area_nome": ticket.area.nome if ticket.area else None,
        "equipamento_id": ticket.equipamento_id,
        "equipamento_nome": ticket.equipamento.nome if ticket.equipamento else None,
        "patrimonio": ticket.patrimonio,
        "numero_serie": ticket.numero_serie,
        "descricao": ticket.descricao,
        "urgencia": ticket.urgencia,
        "status": ticket.status,
        "criado_em": ticket.criado_em.isoformat(),
        "atualizado_em": ticket.atualizado_em.isoformat(),
        "resolvido_em": ticket.resolvido_em.isoformat() if ticket.resolvido_em else None,
        "anexos": [_serializar_anexo(anexo) for anexo in ticket.anexos],
    }


def listar_chamados_usuario(usuario_id: int, status: str | None = None) -> list[dict]:
    consulta = SupportTicket.query.options(
        joinedload(SupportTicket.area), joinedload(SupportTicket.equipamento), joinedload(SupportTicket.anexos)
    ).filter_by(usuario_id=usuario_id)
    if status:
        consulta = consulta.filter(SupportTicket.status == status.lower())
    tickets = consulta.order_by(SupportTicket.criado_em.desc()).all()
    return [serializar_chamado(ticket) for ticket in tickets]


def listar_chamados_admin(
    *,
    status: str | None = None,
    urgencia: str | None = None,
    area_id: int | None = None,
    equipamento_id: int | None = None,
    ordenacao: str = "data",
    ordem: str = "desc",
    page: int = 1,
    per_page: int = 20,
) -> dict:
    consulta = SupportTicket.query.options(
        joinedload(SupportTicket.area),
        joinedload(SupportTicket.equipamento),
        joinedload(SupportTicket.anexos),
    )

    if status:
        if status.lower() not in VALID_STATUSES:
            raise SupportServiceError("Status informado é inválido")
        consulta = consulta.filter(SupportTicket.status == status.lower())
    if urgencia:
        if urgencia.lower() not in VALID_URGENCIAS:
            raise SupportServiceError("Urgência informada é inválida")
        consulta = consulta.filter(SupportTicket.urgencia == urgencia.lower())
    if area_id:
        consulta = consulta.filter(SupportTicket.area_id == area_id)
    if equipamento_id:
        consulta = consulta.filter(SupportTicket.equipamento_id == equipamento_id)

    ordem = ordem.lower()
    if ordenacao == "urgencia":
        prioridade_case = case(
            value=SupportTicket.urgencia,
            whens=URGENCIA_PRIORIDADE,
            else_=0,
        )
        order_clause = prioridade_case.asc() if ordem == "asc" else prioridade_case.desc()
    elif ordenacao == "status":
        prioridade_case = case(
            value=SupportTicket.status,
            whens={valor: idx for idx, valor in enumerate(VALID_STATUSES, start=1)},
            else_=0,
        )
        order_clause = prioridade_case.asc() if ordem == "asc" else prioridade_case.desc()
    else:  # data
        order_clause = (
            SupportTicket.criado_em.asc() if ordem == "asc" else SupportTicket.criado_em.desc()
        )

    consulta = consulta.order_by(order_clause, SupportTicket.criado_em.desc())

    page = max(page, 1)
    per_page = max(1, min(per_page, 100))
    paginacao = consulta.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": [serializar_chamado(ticket) for ticket in paginacao.items],
        "page": paginacao.page,
        "per_page": paginacao.per_page,
        "total": paginacao.total,
        "pages": paginacao.pages,
    }


def atualizar_chamado(ticket_id: int, dados: SupportTicketUpdateSchema) -> SupportTicket:
    ticket = (
        db.session.query(SupportTicket)
        .options(joinedload(SupportTicket.anexos))
        .filter(SupportTicket.id == ticket_id)
        .one_or_none()
    )
    if not ticket:
        raise SupportServiceError("Chamado não encontrado")

    if dados.area_id is not None:
        _validar_lookup_ids(dados.area_id, None)
        ticket.area_id = dados.area_id
    if dados.equipamento_id is not None:
        _validar_lookup_ids(None, dados.equipamento_id)
        ticket.equipamento_id = dados.equipamento_id
    if dados.urgencia is not None:
        ticket.urgencia = dados.urgencia
    if dados.status is not None:
        ticket.status = dados.status
        if dados.status in {"resolvido", "encerrado"} and not ticket.resolvido_em:
            ticket.resolvido_em = datetime.utcnow()
        elif dados.status not in {"resolvido", "encerrado"}:
            ticket.resolvido_em = None
    if dados.patrimonio is not None:
        ticket.patrimonio = dados.patrimonio
    if dados.numero_serie is not None:
        ticket.numero_serie = dados.numero_serie
    if dados.descricao is not None:
        ticket.descricao = dados.descricao

    try:
        db.session.commit()
    except SQLAlchemyError as exc:  # pragma: no cover
        db.session.rollback()
        log.exception("Erro ao atualizar chamado")
        raise SupportServiceError("Não foi possível atualizar o chamado") from exc

    return ticket


def obter_indicadores() -> dict:
    total = SupportTicket.query.count()

    por_status = {
        status: db.session.query(func.count(SupportTicket.id))
        .filter(SupportTicket.status == status)
        .scalar()
        for status in VALID_STATUSES
    }

    por_urgencia = {
        urgencia: db.session.query(func.count(SupportTicket.id))
        .filter(SupportTicket.urgencia == urgencia)
        .scalar()
        for urgencia in VALID_URGENCIAS
    }

    por_area = (
        db.session.query(SupportArea.nome, func.count(SupportTicket.id))
        .outerjoin(SupportTicket, SupportTicket.area_id == SupportArea.id)
        .group_by(SupportArea.id)
        .order_by(SupportArea.nome.asc())
        .all()
    )

    chamados_sem_area = (
        db.session.query(func.count(SupportTicket.id))
        .filter(SupportTicket.area_id.is_(None))
        .scalar()
    )

    por_equipamento = (
        db.session.query(SupportEquipmentType.nome, func.count(SupportTicket.id))
        .outerjoin(SupportTicket, SupportTicket.equipamento_id == SupportEquipmentType.id)
        .group_by(SupportEquipmentType.id)
        .order_by(SupportEquipmentType.nome.asc())
        .all()
    )

    chamados_sem_equipamento = (
        db.session.query(func.count(SupportTicket.id))
        .filter(SupportTicket.equipamento_id.is_(None))
        .scalar()
    )

    resolvidos = (
        SupportTicket.query.filter(SupportTicket.resolvido_em.isnot(None)).all()
    )
    if resolvidos:
        tempos = [
            (ticket.resolvido_em - ticket.criado_em).total_seconds()
            for ticket in resolvidos
            if ticket.resolvido_em and ticket.criado_em
        ]
        media_resolucao = sum(tempos) / len(tempos)
    else:
        media_resolucao = 0.0

    return {
        "total_chamados": total,
        "chamados_por_status": por_status,
        "chamados_por_urgencia": por_urgencia,
        "chamados_por_area": [
            {"nome": nome, "total": total} for nome, total in por_area
        ]
        + (
            [{"nome": "Sem área", "total": chamados_sem_area}]
            if chamados_sem_area
            else []
        ),
        "chamados_por_equipamento": [
            {"nome": nome, "total": total} for nome, total in por_equipamento
        ]
        + (
            [{"nome": "Sem equipamento", "total": chamados_sem_equipamento}]
            if chamados_sem_equipamento
            else []
        ),
        "media_tempo_resolucao_segundos": media_resolucao,
    }
