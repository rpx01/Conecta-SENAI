from flask import Blueprint, jsonify, request
from src.models import db
from src.models.planejamento import (
    PlanejamentoBDItem,
    Local,
    Modalidade,
    Horario,
    CargaHoraria,
    PublicoAlvo,
)

basedados_bp = Blueprint(
    "planejamento_basedados",
    __name__,
    url_prefix="/planejamento-basedados",
)

MODELOS = {
    "local": Local,
    "modalidade": Modalidade,
    "horario": Horario,
    "cargahoraria": CargaHoraria,
    "publico-alvo": PublicoAlvo,
}


@basedados_bp.route("/itens", methods=["GET"])
def get_planejamento_itens():
    itens = PlanejamentoBDItem.query.all()
    return jsonify([item.to_dict() for item in itens])


@basedados_bp.route("/itens", methods=["POST"])
def create_planejamento_item():
    data = request.json or {}
    descricao = data.get("descricao")
    instrutor_id = data.get("instrutor_id")
    if not descricao or not instrutor_id:
        return jsonify({"erro": "Descrição e instrutor_id são obrigatórios"}), 400
    item = PlanejamentoBDItem(descricao=descricao, instrutor_id=instrutor_id)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@basedados_bp.route("/<tipo>", methods=["GET"])
def get_itens_genericos(tipo):
    model = MODELOS.get(tipo)
    if not model:
        return jsonify({"erro": "Tipo inválido"}), 404

    itens = model.query.order_by(model.nome).all()
    return jsonify([item.to_dict() for item in itens])


@basedados_bp.route("/<tipo>", methods=["POST"])
def create_item_generico(tipo):
    model = MODELOS.get(tipo)
    if not model:
        return jsonify({"erro": "Tipo inválido"}), 404

    data = request.json or {}
    nome = data.get("nome")
    if not nome:
        return jsonify({"erro": "Nome é obrigatório"}), 400

    item = model(nome=nome)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@basedados_bp.route("/<tipo>/<int:item_id>", methods=["PUT"])
def update_item_generico(tipo, item_id):
    model = MODELOS.get(tipo)
    if not model:
        return jsonify({"erro": "Tipo inválido"}), 404

    item = model.query.get_or_404(item_id)
    data = request.json or {}
    nome = data.get("nome")
    if not nome:
        return jsonify({"erro": "Nome é obrigatório"}), 400

    item.nome = nome
    db.session.commit()
    return jsonify(item.to_dict())


@basedados_bp.route("/<tipo>/<int:item_id>", methods=["DELETE"])
def delete_item_generico(tipo, item_id):
    model = MODELOS.get(tipo)
    if not model:
        return jsonify({"erro": "Tipo inválido"}), 404

    item = model.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return "", 204

