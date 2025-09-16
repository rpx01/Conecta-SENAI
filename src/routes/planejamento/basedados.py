from flask import Blueprint, jsonify, request
from sqlalchemy import inspect
from src.auth import admin_required
from src.models import db
from src.models.planejamento import (
    PlanejamentoBDItem,
    Local,
    Modalidade,
    Horario,
    CargaHoraria,
    PublicoAlvo,
    PlanejamentoTreinamento,
    TurnoEnum,
)
from src.models import EmailSecretaria
from src.schemas.planejamento import EmailSecretariaSchema

basedados_bp = Blueprint(
    "planejamento_basedados",
    __name__
)

# Mapeamento corrigido para corresponder aos tipos usados no frontend
MODELOS = {
    "treinamento": PlanejamentoTreinamento,
    "local": Local,
    "modalidade": Modalidade,
    "horario": Horario,
    "cargahoraria": CargaHoraria,
    "publico-alvo": PublicoAlvo,
}

email_schema = EmailSecretariaSchema()
emails_schema = EmailSecretariaSchema(many=True)


def ensure_table_exists(model):
    """Cria a tabela do modelo se ela ainda não existir."""
    inspector = inspect(db.engine)
    if not inspector.has_table(model.__tablename__):
        model.__table__.create(db.engine)


@basedados_bp.route("/itens", methods=["GET"])
def get_planejamento_itens():
    """Busca os itens principais da base de dados."""
    ensure_table_exists(PlanejamentoBDItem)
    itens = PlanejamentoBDItem.query.all()
    return jsonify([item.to_dict() for item in itens])


@basedados_bp.route("/emails-secretaria", methods=["GET"])
@admin_required
def listar_emails_secretaria():
    """Lista todos os emails da secretaria."""
    ensure_table_exists(EmailSecretaria)
    emails = EmailSecretaria.query.order_by(EmailSecretaria.id).all()
    return jsonify(emails_schema.dump(emails))


@basedados_bp.route("/emails-secretaria", methods=["POST"])
@admin_required
def criar_email_secretaria():
    """Cria um novo email da secretaria."""
    ensure_table_exists(EmailSecretaria)
    data = request.json or {}
    nome = data.get("nome")
    email = data.get("email")
    if not nome or not email:
        return jsonify({"erro": "Nome e e-mail são obrigatórios"}), 400
    if EmailSecretaria.query.filter_by(email=email).first():
        return jsonify({"erro": "E-mail já cadastrado"}), 409
    item = EmailSecretaria(nome=nome, email=email)
    db.session.add(item)
    db.session.commit()
    return email_schema.dump(item), 201


@basedados_bp.route("/emails-secretaria/<int:item_id>", methods=["PUT"])
@admin_required
def atualizar_email_secretaria(item_id):
    """Atualiza um email existente."""
    ensure_table_exists(EmailSecretaria)
    item = db.session.get(EmailSecretaria, item_id)
    if not item:
        return jsonify({"erro": "E-mail não encontrado"}), 404
    data = request.json or {}
    nome = data.get("nome")
    email = data.get("email")
    if not nome or not email:
        return jsonify({"erro": "Nome e e-mail são obrigatórios"}), 400
    if EmailSecretaria.query.filter(
        EmailSecretaria.email == email, EmailSecretaria.id != item_id
    ).first():
        return jsonify({"erro": "E-mail já cadastrado"}), 409
    item.nome = nome
    item.email = email
    db.session.commit()
    return email_schema.dump(item)


@basedados_bp.route("/emails-secretaria/<int:item_id>", methods=["DELETE"])
@admin_required
def deletar_email_secretaria(item_id):
    """Exclui um email da secretaria."""
    ensure_table_exists(EmailSecretaria)
    item = db.session.get(EmailSecretaria, item_id)
    if not item:
        return jsonify({"erro": "E-mail não encontrado"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"mensagem": "E-mail excluído com sucesso"}), 200


@basedados_bp.route("/itens", methods=["POST"])
def create_planejamento_item():
    """Cria um novo item principal na base de dados."""
    ensure_table_exists(PlanejamentoBDItem)
    data = request.json or {}
    descricao = data.get("descricao")
    instrutor_id = data.get("instrutor_id")
    if not descricao or not instrutor_id:
        mensagem = "Descrição e instrutor_id são obrigatórios"
        return jsonify({"erro": mensagem}), 400
    item = PlanejamentoBDItem(descricao=descricao, instrutor_id=instrutor_id)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@basedados_bp.route("/<tipo>", methods=["GET"])
def get_itens_genericos(tipo):
    """Busca todos os itens de um tipo específico (Local, Modalidade, etc.)."""
    model = MODELOS.get(tipo)
    if not model:
        return jsonify({"erro": "Tipo inválido"}), 404
    ensure_table_exists(model)
    itens = model.query.order_by(model.nome).all()
    return jsonify([item.to_dict() for item in itens])


@basedados_bp.route("/<tipo>", methods=["POST"])
def create_item_generico(tipo):
    """Cria um novo item de um tipo específico."""
    model = MODELOS.get(tipo)
    if not model:
        return jsonify({"erro": "Tipo inválido"}), 404
    ensure_table_exists(model)
    data = request.json or {}
    nome = data.get("nome")
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório"}), 400

    # Verifica se já existe um item com o mesmo nome
    if model.query.filter_by(nome=nome).first():
        return jsonify({"erro": f"O item '{nome}' já existe."}), 409

    if tipo == "treinamento":
        item = model(nome=nome, carga_horaria=data.get("carga_horaria"))
    elif tipo == "horario":
        turno = data.get("turno")
        if not turno:
            return jsonify({"erro": "O campo 'turno' é obrigatório"}), 400
        if turno not in [t.value for t in TurnoEnum]:
            return jsonify({"erro": "Turno inválido"}), 400
        item = model(nome=nome, turno=turno)
    else:
        item = model(nome=nome)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@basedados_bp.route("/<tipo>/<int:item_id>", methods=["PUT"])
def update_item_generico(tipo, item_id):
    """Atualiza um item de um tipo específico."""
    model = MODELOS.get(tipo)
    if not model:
        return jsonify({"erro": "Tipo inválido"}), 404
    ensure_table_exists(model)
    item = db.session.get(model, item_id)
    if not item:
        return jsonify({"erro": "Item não encontrado"}), 404

    data = request.json or {}
    nome = data.get("nome")
    if not nome:
        return jsonify({"erro": "O campo 'nome' é obrigatório"}), 400

    item.nome = nome
    if tipo == "treinamento":
        item.carga_horaria = data.get("carga_horaria")
    elif tipo == "horario":
        if data.get("turno") is not None:
            turno = data.get("turno")
            if turno not in [t.value for t in TurnoEnum]:
                return jsonify({"erro": "Turno inválido"}), 400
            item.turno = turno
    db.session.commit()
    return jsonify(item.to_dict())


@basedados_bp.route("/<tipo>/<int:item_id>", methods=["DELETE"])
def delete_item_generico(tipo, item_id):
    """Exclui um item de um tipo específico."""
    model = MODELOS.get(tipo)
    if not model:
        return jsonify({"erro": "Tipo inválido"}), 404
    ensure_table_exists(model)
    item = db.session.get(model, item_id)
    if not item:
        return jsonify({"erro": "Item não encontrado"}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({"mensagem": "Item excluído com sucesso"}), 200
