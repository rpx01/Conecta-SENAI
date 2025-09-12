from flask import Blueprint, jsonify, request
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from src.auth import admin_required
from src.models import db
from src.models.secretaria_treinamentos import SecretariaTreinamentos
from src.schemas.secretaria_treinamentos import SecretariaTreinamentosSchema

secretaria_bp = Blueprint("treinamentos_secretaria", __name__)

schema = SecretariaTreinamentosSchema()
schemas = SecretariaTreinamentosSchema(many=True)


def ensure_table_exists(model) -> None:
    """Cria a tabela do modelo caso não exista."""
    inspector = inspect(db.engine)
    if not inspector.has_table(model.__tablename__):
        model.__table__.create(db.engine)


@secretaria_bp.route("", methods=["GET"])
@admin_required
def listar_contatos():
    ensure_table_exists(SecretariaTreinamentos)
    contatos = (
        SecretariaTreinamentos.query.order_by(SecretariaTreinamentos.id).all()
    )
    return jsonify(schemas.dump(contatos))


@secretaria_bp.route("", methods=["POST"])
@admin_required
def criar_contato():
    ensure_table_exists(SecretariaTreinamentos)
    data = request.get_json() or {}
    erros = schema.validate(data)
    if erros:
        return jsonify({"erro": erros}), 400
    if SecretariaTreinamentos.query.filter_by(email=data.get("email")).first():
        return jsonify({"erro": "E-mail já cadastrado"}), 409
    contato = SecretariaTreinamentos(nome=data["nome"], email=data["email"])
    try:
        db.session.add(contato)
        db.session.commit()
        return schema.dump(contato), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao salvar contato"}), 500


@secretaria_bp.route("/<int:contato_id>", methods=["PUT"])
@admin_required
def atualizar_contato(contato_id):
    ensure_table_exists(SecretariaTreinamentos)
    contato = db.session.get(SecretariaTreinamentos, contato_id)
    if not contato:
        return jsonify({"erro": "Contato não encontrado"}), 404
    data = request.get_json() or {}
    erros = schema.validate(data)
    if erros:
        return jsonify({"erro": erros}), 400
    if (
        SecretariaTreinamentos.query.filter(
            SecretariaTreinamentos.email == data.get("email"),
            SecretariaTreinamentos.id != contato_id,
        ).first()
    ):
        return jsonify({"erro": "E-mail já cadastrado"}), 409
    contato.nome = data["nome"]
    contato.email = data["email"]
    try:
        db.session.commit()
        return schema.dump(contato)
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao atualizar contato"}), 500


@secretaria_bp.route("/<int:contato_id>", methods=["DELETE"])
@admin_required
def excluir_contato(contato_id):
    ensure_table_exists(SecretariaTreinamentos)
    contato = db.session.get(SecretariaTreinamentos, contato_id)
    if not contato:
        return jsonify({"erro": "Contato não encontrado"}), 404
    try:
        db.session.delete(contato)
        db.session.commit()
        return jsonify({"mensagem": "Contato excluído com sucesso"}), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao excluir contato"}), 500
