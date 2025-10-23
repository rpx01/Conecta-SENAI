"""Regras de negócio para o módulo de chamados de TI."""
from __future__ import annotations

import os
import re
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from flask import current_app
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from src.models import (
    Ticket,
    TicketAttachment,
    TicketAsset,
    TicketCategory,
    TicketComment,
    TicketLocation,
    TicketPriority,
    TicketSLA,
    TicketStatus,
    User,
    db,
)
from src.schemas.chamados import TicketSchema
from src.services.notification_service import send_ticket_email

MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_TOTAL_SIZE = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "csv",
    "txt",
    "log",
    "docx",
    "xlsx",
}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "text/csv",
    "text/plain",
    "application/octet-stream",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

_SANITIZE_RE = re.compile(r"<[^>]+>")


def _uploads_dir() -> Path:
    cfg_path = (
        current_app.config.get("UPLOADS_DIR")
        or os.getenv("UPLOADS_DIR")
        or "uploads/chamados"
    )
    base_path = Path(cfg_path)
    if not base_path.is_absolute():
        base_path = Path(current_app.root_path).parent / base_path
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path


def _sanitize(texto: str) -> str:
    return _SANITIZE_RE.sub("", texto or "").strip()


def _load_user(user_id: int) -> Optional[User]:
    return db.session.get(User, user_id)


def _default_status() -> TicketStatus:
    status = TicketStatus.query.filter_by(nome="aberto").first()
    if not status:
        raise ValueError("Status padrão 'aberto' não configurado")
    return status


def _ensure_priority(priority_id: Optional[int]) -> TicketPriority:
    if priority_id:
        prioridade = db.session.get(TicketPriority, priority_id)
        if prioridade and prioridade.ativo:
            return prioridade
        raise ValueError("Prioridade inválida ou inativa")
    prioridade = TicketPriority.query.filter_by(nome="media").first()
    if not prioridade:
        raise ValueError("Prioridade padrão 'media' não configurada")
    return prioridade


def _ensure_category(category_id: int) -> TicketCategory:
    categoria = db.session.get(TicketCategory, category_id)
    if not categoria or not categoria.ativo:
        raise ValueError("Categoria inválida ou inativa")
    return categoria


def _ensure_status(status_id: int) -> TicketStatus:
    status = db.session.get(TicketStatus, status_id)
    if not status or not status.ativo:
        raise ValueError("Status inválido ou inativo")
    return status


def _ensure_location(location_id: Optional[int]) -> Optional[TicketLocation]:
    if location_id is None:
        return None
    location = db.session.get(TicketLocation, location_id)
    if not location or not location.ativo:
        raise ValueError("Local inválido ou inativo")
    return location


def _ensure_asset(asset_id: Optional[int]) -> Optional[TicketAsset]:
    if asset_id is None:
        return None
    asset = db.session.get(TicketAsset, asset_id)
    if not asset or not asset.ativo:
        raise ValueError("Ativo inválido ou inativo")
    return asset


def _read_file_size(file: FileStorage) -> int:
    pos = file.stream.tell()
    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(pos)
    return size


def _validate_files(files: Sequence[FileStorage]) -> None:
    total = 0
    for file in files:
        if not file or not getattr(file, "filename", ""):
            continue
        size = _read_file_size(file)
        file.stream.seek(0)
        if size > MAX_FILE_SIZE:
            raise ValueError("Arquivo excede o limite de 10MB")
        total += size
        if total > MAX_TOTAL_SIZE:
            raise ValueError("Limite total de 50MB excedido")
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Extensão de arquivo não permitida: {ext}")
        content_type = file.mimetype or ""
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(f"Tipo de conteúdo não permitido: {content_type}")


def _save_files(
    ticket: Ticket, user_id: int, files: Sequence[FileStorage]
) -> List[TicketAttachment]:
    saved: List[TicketAttachment] = []
    base_dir = _uploads_dir()
    for file in files:
        if not file or not getattr(file, "filename", ""):
            continue
        filename = secure_filename(file.filename)
        if not filename:
            continue
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        path = base_dir / unique_name
        size_bytes = _read_file_size(file)
        file.stream.seek(0)
        file.save(path)
        attachment = TicketAttachment(
            ticket=ticket,
            filename=filename,
            content_type=file.mimetype or "application/octet-stream",
            size_bytes=size_bytes,
            storage_path=str(path.relative_to(base_dir.parent)),
            uploaded_by_id=user_id,
        )
        db.session.add(attachment)
        saved.append(attachment)
    return saved


def _compute_sla(ticket: Ticket) -> None:
    consulta = TicketSLA.query
    sla = consulta.filter_by(
        categoria_id=ticket.categoria_id, prioridade_id=ticket.prioridade_id
    ).first()
    if not sla:
        sla = consulta.filter_by(categoria_id=None, prioridade_id=ticket.prioridade_id).first()
    if sla:
        ticket.sla_horas = sla.horas
        ticket.prazo_sla = ticket.created_at + timedelta(hours=sla.horas)


def _notify_ticket_creation(ticket: Ticket) -> None:
    admins = (
        User.query.filter(User.tipo == "admin")
        .with_entities(User.email)
        .all()
    )
    destinatarios = [email for (email,) in admins if email]
    solicitante_email = getattr(ticket.solicitante, "email", None)
    if solicitante_email:
        destinatarios.append(solicitante_email)
    if not destinatarios:
        return
    context = {"ticket": TicketSchema().dump(ticket)}
    send_ticket_email(
        subject=f"Novo chamado #{ticket.id}: {ticket.titulo}",
        template="chamados/novo_ticket.html.j2",
        context=context,
        to=destinatarios,
    )


def _notify_ticket_status(ticket: Ticket, antigo_status: Optional[str]) -> None:
    destinatarios = set()
    if ticket.solicitante and ticket.solicitante.email:
        destinatarios.add(ticket.solicitante.email)
    if ticket.atribuido and ticket.atribuido.email:
        destinatarios.add(ticket.atribuido.email)
    if not destinatarios:
        return
    context = {
        "ticket": TicketSchema().dump(ticket),
        "status_anterior": antigo_status,
    }
    send_ticket_email(
        subject=f"Atualização do chamado #{ticket.id}",
        template="chamados/status_ticket.html.j2",
        context=context,
        to=list(destinatarios),
    )


def create_ticket(user_id: int, data: dict, files: Sequence[FileStorage]) -> Ticket:
    categoria = _ensure_category(data["categoria_id"])
    prioridade = _ensure_priority(data.get("prioridade_id"))
    status = _default_status()

    ticket = Ticket(
        titulo=data["titulo"].strip(),
        descricao=data["descricao"].strip(),
        categoria=categoria,
        prioridade=prioridade,
        status=status,
        solicitante_id=user_id,
        location_id=None,
        asset_id=None,
    )
    if data.get("location_id") is not None:
        ticket.location_id = _ensure_location(data["location_id"]).id
    if data.get("asset_id") is not None:
        ticket.asset_id = _ensure_asset(data["asset_id"]).id

    db.session.add(ticket)
    db.session.flush()

    if files:
        _validate_files(files)
        _save_files(ticket, user_id, files)

    _compute_sla(ticket)
    db.session.commit()

    _notify_ticket_creation(ticket)
    return ticket


def list_my_tickets(user_id: int, filtros: dict, paginacao: dict) -> dict:
    query = (
        Ticket.query.options(
            joinedload(Ticket.categoria),
            joinedload(Ticket.prioridade),
            joinedload(Ticket.status),
        )
        .filter(Ticket.solicitante_id == user_id)
        .order_by(Ticket.created_at.desc())
    )

    if filtros.get("status_id"):
        query = query.filter(Ticket.status_id == filtros["status_id"])
    if filtros.get("categoria_id"):
        query = query.filter(Ticket.categoria_id == filtros["categoria_id"])
    if filtros.get("prioridade_id"):
        query = query.filter(Ticket.prioridade_id == filtros["prioridade_id"])
    if filtros.get("q"):
        termo = f"%{filtros['q'].strip()}%"
        query = query.filter(Ticket.titulo.ilike(termo))

    page_raw = paginacao.get("page")
    page = 1
    if page_raw not in (None, ""):
        try:
            page = max(int(page_raw), 1)
        except (TypeError, ValueError):
            page = 1

    page_size_raw = paginacao.get("page_size")
    page_size = 20
    if page_size_raw not in (None, ""):
        try:
            page_size = max(min(int(page_size_raw), 100), 1)
        except (TypeError, ValueError):
            page_size = 20

    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    schema = TicketSchema(many=True)
    return {
        "items": schema.dump(pagination.items),
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total,
    }


def _can_access(user: User, ticket: Ticket) -> bool:
    if user.tipo == "admin":
        return True
    if ticket.solicitante_id == user.id:
        return True
    if ticket.atribuido_id and ticket.atribuido_id == user.id:
        return True
    return False


def get_ticket_detail(user_id: int, ticket_id: int) -> Ticket:
    user = _load_user(user_id)
    if not user:
        raise ValueError("Usuário não encontrado")
    ticket = (
        Ticket.query.options(
            joinedload(Ticket.categoria),
            joinedload(Ticket.prioridade),
            joinedload(Ticket.status),
            joinedload(Ticket.solicitante),
            joinedload(Ticket.atribuido),
            joinedload(Ticket.comentarios).joinedload(TicketComment.autor),
            joinedload(Ticket.anexos).joinedload(TicketAttachment.uploader),
            joinedload(Ticket.local),
            joinedload(Ticket.ativo_relacionado),
        )
        .filter_by(id=ticket_id)
        .first()
    )
    if not ticket:
        raise ValueError("Ticket não encontrado")
    if not _can_access(user, ticket):
        raise PermissionError("Permissão negada")
    return ticket


def add_comment(user_id: int, ticket_id: int, mensagem: str) -> TicketComment:
    ticket = get_ticket_detail(user_id, ticket_id)
    mensagem_limpa = _sanitize(mensagem)
    if not mensagem_limpa:
        raise ValueError("Mensagem inválida")
    comentario = TicketComment(
        ticket_id=ticket.id,
        autor_id=user_id,
        mensagem=mensagem_limpa,
    )
    db.session.add(comentario)
    db.session.commit()
    return comentario


def add_attachments(user_id: int, ticket_id: int, files: Sequence[FileStorage]) -> List[TicketAttachment]:
    ticket = get_ticket_detail(user_id, ticket_id)
    _validate_files(files)
    anexos = _save_files(ticket, user_id, files)
    db.session.commit()
    return anexos


def admin_list_open_tickets(filtros: dict, paginacao: dict) -> dict:
    abertos = TicketStatus.query.filter(
        TicketStatus.nome.in_(["aberto", "em_atendimento", "pendente"])
    ).all()
    ids_abertos = [status.id for status in abertos]
    if not ids_abertos:
        ids_abertos = [
            status.id for status in TicketStatus.query.filter(TicketStatus.ativo.is_(True)).all()
        ]
    query = (
        Ticket.query.options(
            joinedload(Ticket.categoria),
            joinedload(Ticket.prioridade),
            joinedload(Ticket.status),
            joinedload(Ticket.atribuido),
            joinedload(Ticket.solicitante),
        )
        .order_by(Ticket.created_at.desc())
    )
    if ids_abertos:
        query = query.filter(Ticket.status_id.in_(ids_abertos))

    if filtros.get("status_id"):
        query = query.filter(Ticket.status_id == filtros["status_id"])
    if filtros.get("categoria_id"):
        query = query.filter(Ticket.categoria_id == filtros["categoria_id"])
    if filtros.get("prioridade_id"):
        query = query.filter(Ticket.prioridade_id == filtros["prioridade_id"])
    if filtros.get("atribuido_id"):
        query = query.filter(Ticket.atribuido_id == filtros["atribuido_id"])
    if filtros.get("q"):
        termo = f"%{filtros['q'].strip()}%"
        query = query.filter(Ticket.titulo.ilike(termo))

    page_raw = paginacao.get("page")
    page = 1
    if page_raw not in (None, ""):
        try:
            page = max(int(page_raw), 1)
        except (TypeError, ValueError):
            page = 1

    page_size_raw = paginacao.get("page_size")
    page_size = 20
    if page_size_raw not in (None, ""):
        try:
            page_size = max(min(int(page_size_raw), 100), 1)
        except (TypeError, ValueError):
            page_size = 20

    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    schema = TicketSchema(many=True)
    return {
        "items": schema.dump(pagination.items),
        "page": pagination.page,
        "pages": pagination.pages,
        "total": pagination.total,
    }


def assign_ticket(admin_id: int, ticket_id: int, atribuido_id: int) -> Ticket:
    admin = _load_user(admin_id)
    if not admin or admin.tipo != "admin":
        raise PermissionError("Somente administradores podem atribuir chamados")
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        raise ValueError("Ticket não encontrado")
    atribuido = _load_user(atribuido_id)
    if not atribuido:
        raise ValueError("Usuário atribuído inválido")
    ticket.atribuido_id = atribuido_id
    db.session.commit()
    ticket = get_ticket_detail(admin_id, ticket_id)
    _notify_ticket_status(ticket, ticket.status.nome if ticket.status else None)
    return ticket


def update_status(actor_id: int, ticket_id: int, status_id: int) -> Ticket:
    user = _load_user(actor_id)
    if not user:
        raise ValueError("Usuário inválido")
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        raise ValueError("Ticket não encontrado")
    if not _can_access(user, ticket):
        raise PermissionError("Permissão negada")
    status = _ensure_status(status_id)
    antigo_status = ticket.status.nome if ticket.status else None
    ticket.status = status
    ticket.atualizar_resolucao(status.nome)
    db.session.commit()
    ticket = get_ticket_detail(actor_id, ticket_id)
    _notify_ticket_status(ticket, antigo_status)
    return ticket


def update_priority(admin_id: int, ticket_id: int, prioridade_id: int) -> Ticket:
    admin = _load_user(admin_id)
    if not admin or admin.tipo != "admin":
        raise PermissionError("Somente administradores podem alterar a prioridade")
    ticket = db.session.get(Ticket, ticket_id)
    if not ticket:
        raise ValueError("Ticket não encontrado")
    prioridade = _ensure_priority(prioridade_id)
    ticket.prioridade = prioridade
    _compute_sla(ticket)
    db.session.commit()
    return get_ticket_detail(admin_id, ticket_id)


def compute_indicators(periodo_dias: int = 30) -> dict:
    limite = datetime.utcnow() - timedelta(days=periodo_dias)
    recentes_base = Ticket.query.filter(Ticket.created_at >= limite)

    por_status = (
        recentes_base.join(TicketStatus)
        .with_entities(TicketStatus.nome, func.count(Ticket.id))
        .group_by(TicketStatus.nome)
        .all()
    )
    por_categoria = (
        recentes_base.join(TicketCategory)
        .with_entities(TicketCategory.nome, func.count(Ticket.id))
        .group_by(TicketCategory.nome)
        .all()
    )
    por_prioridade = (
        recentes_base.join(TicketPriority)
        .with_entities(TicketPriority.nome, func.count(Ticket.id))
        .group_by(TicketPriority.nome)
        .all()
    )

    resolvidos = (
        recentes_base.filter(Ticket.resolvido_em.isnot(None))
        .with_entities(Ticket)
        .all()
    )
    tempos_resolucao = []
    dentro_sla = 0
    fora_sla = 0
    for (ticket,) in resolvidos:
        if ticket.resolvido_em and ticket.created_at:
            delta = ticket.resolvido_em - ticket.created_at
            tempos_resolucao.append(delta.total_seconds() / 3600)
        if ticket.prazo_sla and ticket.resolvido_em:
            if ticket.resolvido_em <= ticket.prazo_sla:
                dentro_sla += 1
            else:
                fora_sla += 1

    media_resolucao = sum(tempos_resolucao) / len(tempos_resolucao) if tempos_resolucao else 0

    envelhecimento_faixas = defaultdict(int)
    agora = datetime.utcnow()
    recentes_lista = recentes_base.all()
    for ticket in recentes_lista:
        idade_dias = (agora - ticket.created_at).days
        if idade_dias <= 2:
            envelhecimento_faixas["0-2"] += 1
        elif idade_dias <= 7:
            envelhecimento_faixas["3-7"] += 1
        elif idade_dias <= 14:
            envelhecimento_faixas["8-14"] += 1
        else:
            envelhecimento_faixas[">14"] += 1

    return {
        "periodo_dias": periodo_dias,
        "por_status": {nome: total for nome, total in por_status},
        "por_categoria": {nome: total for nome, total in por_categoria},
        "por_prioridade": {nome: total for nome, total in por_prioridade},
        "media_resolucao_horas": round(media_resolucao, 2),
        "sla": {
            "dentro": dentro_sla,
            "fora": fora_sla,
        },
        "envelhecimento": dict(envelhecimento_faixas),
    }


def resolve_attachment_path(attachment: TicketAttachment) -> Optional[Path]:
    """Retorna o caminho absoluto do arquivo de anexo se disponível."""
    caminho = attachment.storage_path
    if not caminho:
        return None
    base_dir = _uploads_dir()
    destino = Path(base_dir.parent) / caminho
    if destino.exists():
        return destino
    return None
