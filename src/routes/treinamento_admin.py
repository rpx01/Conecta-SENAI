from flask import Blueprint, request, jsonify
from src.models import db
from src.models.treinamento import Treinamento, MaterialDidatico
from src.auth import admin_required

admin_treinamento_bp = Blueprint('admin_treinamento', __name__)

# --- CRUD para Catálogo de Treinamentos ---

@admin_treinamento_bp.route('/treinamentos', methods=['GET'])
@admin_required
def listar_treinamentos():
    treinamentos = Treinamento.query.order_by(Treinamento.nome).all()
    return jsonify([t.to_dict_full() for t in treinamentos])

@admin_treinamento_bp.route('/treinamentos/<int:id>', methods=['GET'])
@admin_required
def obter_treinamento(id):
    treinamento = Treinamento.query.get_or_404(id)
    return jsonify(treinamento.to_dict_full())

@admin_treinamento_bp.route('/treinamentos', methods=['POST'])
@admin_required
def criar_treinamento():
    dados = request.get_json()
    if not dados.get('nome') or not dados.get('carga_horaria') or not dados.get('max_alunos'):
        return jsonify({"erro": "Campos obrigatórios em falta"}), 400

    novo_treinamento = Treinamento(
        nome=dados['nome'],
        codigo=dados.get('codigo'),
        carga_horaria=dados['carga_horaria'],
        max_alunos=dados['max_alunos']
    )
    db.session.add(novo_treinamento)

    if dados.get('materiais'):
        for mat in dados['materiais']:
            if mat.get('url'):
                db.session.add(
                    MaterialDidatico(
                        descricao=mat.get('descricao', 'Material'),
                        url=mat['url'],
                        treinamento=novo_treinamento,
                    )
                )

    db.session.commit()
    return jsonify(novo_treinamento.to_dict_full()), 201

@admin_treinamento_bp.route('/treinamentos/<int:id>', methods=['PUT'])
@admin_required
def atualizar_treinamento(id):
    treinamento = Treinamento.query.get_or_404(id)
    dados = request.get_json()

    treinamento.nome = dados.get('nome', treinamento.nome)
    treinamento.codigo = dados.get('codigo', treinamento.codigo)
    treinamento.carga_horaria = dados.get('carga_horaria', treinamento.carga_horaria)
    treinamento.max_alunos = dados.get('max_alunos', treinamento.max_alunos)

    MaterialDidatico.query.filter_by(treinamento_id=id).delete()
    if dados.get('materiais'):
        for mat in dados['materiais']:
            if mat.get('url'):
                db.session.add(
                    MaterialDidatico(
                        descricao=mat.get('descricao', 'Material'),
                        url=mat['url'],
                        treinamento_id=id,
                    )
                )

    db.session.commit()
    return jsonify(treinamento.to_dict_full())

@admin_treinamento_bp.route('/treinamentos/<int:id>', methods=['DELETE'])
@admin_required
def excluir_treinamento(id):
    treinamento = Treinamento.query.get_or_404(id)
    db.session.delete(treinamento)
    db.session.commit()
    return '', 204
