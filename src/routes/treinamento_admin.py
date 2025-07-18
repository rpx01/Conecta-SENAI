from flask import Blueprint, request, jsonify
from src.models import db
from src.models.treinamento import Treinamento, MaterialDidatico
from src.auth import admin_required, login_required

admin_treinamento_bp = Blueprint('admin_treinamento', __name__, url_prefix='/admin')


@admin_treinamento_bp.route('/treinamentos', methods=['GET'])
@login_required
def listar_todos():
    treinamentos = Treinamento.query.order_by(Treinamento.nome).all()
    return jsonify([t.to_dict() for t in treinamentos])


@admin_treinamento_bp.route('/treinamentos/<int:id>', methods=['GET'])
@login_required
def obter_treinamento(id):
    treinamento = db.session.get(Treinamento, id)
    if not treinamento:
        return jsonify({'erro': 'Treinamento não encontrado'}), 404
    return jsonify(treinamento.to_dict_full())


@admin_treinamento_bp.route('/treinamentos', methods=['POST'])
@admin_required
def criar_treinamento():
    data = request.json or {}
    nome = (data.get('nome') or '').strip()
    codigo = (data.get('codigo') or '').strip() or None
    carga_horaria = data.get('carga_horaria')
    max_alunos = data.get('max_alunos')
    materiais = data.get('materiais', [])

    if not nome or carga_horaria is None or max_alunos is None:
        return jsonify({'erro': 'Dados incompletos'}), 400

    if Treinamento.query.filter_by(nome=nome).first():
        return jsonify({'erro': 'Treinamento já existe'}), 400

    treinamento = Treinamento(
        nome=nome,
        codigo=codigo,
        carga_horaria=carga_horaria,
        max_alunos=max_alunos,
    )
    db.session.add(treinamento)
    db.session.flush()

    for mat in materiais:
        desc = (mat.get('descricao') or '').strip()
        url = (mat.get('url') or '').strip() or None
        if desc:
            db.session.add(MaterialDidatico(treinamento_id=treinamento.id, descricao=desc, url=url))

    db.session.commit()
    return jsonify(treinamento.to_dict()), 201


@admin_treinamento_bp.route('/treinamentos/<int:id>', methods=['PUT'])
@admin_required
def atualizar_treinamento(id):
    treinamento = db.session.get(Treinamento, id)
    if not treinamento:
        return jsonify({'erro': 'Treinamento não encontrado'}), 404

    data = request.json or {}
    if 'nome' in data:
        nome = (data.get('nome') or '').strip()
        if not nome:
            return jsonify({'erro': 'Nome não pode ser vazio'}), 400
        existente = Treinamento.query.filter_by(nome=nome).first()
        if existente and existente.id != id:
            return jsonify({'erro': 'Já existe treinamento com este nome'}), 400
        treinamento.nome = nome

    if 'codigo' in data:
        treinamento.codigo = (data.get('codigo') or '').strip() or None

    if 'carga_horaria' in data and data.get('carga_horaria') is not None:
        treinamento.carga_horaria = data.get('carga_horaria')

    if 'max_alunos' in data and data.get('max_alunos') is not None:
        treinamento.max_alunos = data.get('max_alunos')

    if 'materiais' in data:
        treinamento.materiais.delete()
        for mat in data.get('materiais') or []:
            desc = (mat.get('descricao') or '').strip()
            url = (mat.get('url') or '').strip() or None
            if desc:
                treinamento.materiais.append(MaterialDidatico(descricao=desc, url=url))

    db.session.commit()
    return jsonify(treinamento.to_dict())


@admin_treinamento_bp.route('/treinamentos/<int:id>', methods=['DELETE'])
@admin_required
def remover_treinamento(id):
    treinamento = db.session.get(Treinamento, id)
    if not treinamento:
        return jsonify({'erro': 'Treinamento não encontrado'}), 404
    db.session.delete(treinamento)
    db.session.commit()
    return jsonify({'mensagem': 'Treinamento removido'})
