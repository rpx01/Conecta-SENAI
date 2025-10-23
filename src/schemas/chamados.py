"""Schemas Marshmallow para o módulo de chamados de TI."""
from __future__ import annotations

from marshmallow import Schema, fields, validate


class CategoriaSchema(Schema):
    id = fields.Int(dump_only=True)
    nome = fields.Str(required=True)
    descricao = fields.Str(allow_none=True)
    ativo = fields.Bool(load_default=True)


class PrioridadeSchema(Schema):
    id = fields.Int(dump_only=True)
    nome = fields.Str(required=True)
    peso = fields.Int(load_default=0)
    ativo = fields.Bool(load_default=True)


class StatusSchema(Schema):
    id = fields.Int(dump_only=True)
    nome = fields.Str(required=True)
    ordem = fields.Int(load_default=0)
    ativo = fields.Bool(load_default=True)


class LocationSchema(Schema):
    id = fields.Int(dump_only=True)
    nome = fields.Str(required=True)
    ativo = fields.Bool(load_default=True)


class AssetSchema(Schema):
    id = fields.Int(dump_only=True)
    tag = fields.Str(required=True)
    descricao = fields.Str(allow_none=True)
    ativo = fields.Bool(load_default=True)


class SLASchema(Schema):
    id = fields.Int(dump_only=True)
    categoria_id = fields.Int(allow_none=True)
    prioridade_id = fields.Int(required=True)
    horas = fields.Int(required=True, validate=validate.Range(min=1))


class TicketAttachmentSchema(Schema):
    id = fields.Int(dump_only=True)
    filename = fields.Str()
    content_type = fields.Str()
    size_bytes = fields.Int()
    storage_path = fields.Str(load_only=True)
    uploaded_by_id = fields.Int()
    created_at = fields.DateTime()


class TicketCommentSchema(Schema):
    id = fields.Int(dump_only=True)
    ticket_id = fields.Int()
    autor_id = fields.Int()
    mensagem = fields.Str()
    created_at = fields.DateTime()
    autor_nome = fields.Method("get_autor_nome")

    def get_autor_nome(self, obj):
        autor = getattr(obj, "autor", None)
        return getattr(autor, "nome", None)


class TicketCommentCreateSchema(Schema):
    mensagem = fields.Str(required=True, validate=validate.Length(min=1, max=5000))


class TicketCreateSchema(Schema):
    titulo = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    descricao = fields.Str(required=True, validate=validate.Length(min=10))
    categoria_id = fields.Int(required=True)
    prioridade_id = fields.Int(required=True)
    location_id = fields.Int(allow_none=True)
    asset_id = fields.Int(allow_none=True)


class TicketUpdateSchema(Schema):
    status_id = fields.Int(load_default=None)
    prioridade_id = fields.Int(load_default=None)
    atribuido_id = fields.Int(load_default=None)
    descricao = fields.Str(load_default=None)


class TicketSchema(Schema):
    id = fields.Int()
    titulo = fields.Str()
    descricao = fields.Str()
    categoria_id = fields.Int()
    categoria_nome = fields.Method("get_categoria")
    prioridade_id = fields.Int()
    prioridade_nome = fields.Method("get_prioridade")
    status_id = fields.Int()
    status_nome = fields.Method("get_status")
    solicitante_id = fields.Int()
    solicitante_nome = fields.Method("get_solicitante")
    atribuido_id = fields.Int(allow_none=True)
    atribuido_nome = fields.Method("get_atribuido")
    location_id = fields.Int(allow_none=True)
    location_nome = fields.Method("get_location")
    asset_id = fields.Int(allow_none=True)
    asset_tag = fields.Method("get_asset")
    sla_horas = fields.Int(allow_none=True)
    prazo_sla = fields.DateTime(allow_none=True)
    resolvido_em = fields.DateTime(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    comentarios = fields.Nested(TicketCommentSchema, many=True)
    anexos = fields.Nested(TicketAttachmentSchema, many=True)

    def get_categoria(self, obj):
        categoria = getattr(obj, "categoria", None)
        return getattr(categoria, "nome", None)

    def get_prioridade(self, obj):
        prioridade = getattr(obj, "prioridade", None)
        return getattr(prioridade, "nome", None)

    def get_status(self, obj):
        status = getattr(obj, "status", None)
        return getattr(status, "nome", None)

    def get_solicitante(self, obj):
        solicitante = getattr(obj, "solicitante", None)
        return getattr(solicitante, "nome", None)

    def get_atribuido(self, obj):
        atribuido = getattr(obj, "atribuido", None)
        return getattr(atribuido, "nome", None)

    def get_location(self, obj):
        local = getattr(obj, "local", None)
        return getattr(local, "nome", None)

    def get_asset(self, obj):
        asset = getattr(obj, "ativo_relacionado", None)
        return getattr(asset, "tag", None)
