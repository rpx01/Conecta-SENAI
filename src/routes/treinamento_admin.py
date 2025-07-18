from flask import Blueprint, request, jsonify
from src.models import db
from src.models.treinamento import Treinamento, MaterialDidatico
from src.schemas.treinamento import TreinamentoCreateSchema
from src.auth import admin_required
from pydantic import ValidationError

admin_treinamento_bp = Blueprint('admin_treinamento', __name__)

# ROTA GET (LISTAR TODOS) - CORRIGE O ERRO 404
@admin_treinamento_bp.route('/treinamentos', methods=['GET'])
@admin_required
def listar_treinamentos():
    try:
        treinamentos = Treinamento.query.order_by(Treinamento.nome).all()
        return jsonify([t.to_dict_full() for t in treinamentos]), 200
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

# ROTA GET (BUSCAR UM) - PARA O BOTÃO EDITAR
@admin_treinamento_bp.route('/treinamentos/<int:id>', methods=['GET'])
@admin_required
def obter_treinamento(id):
    treinamento = Treinamento.query.get_or_404(id)
    return jsonify(treinamento.to_dict_full())

# ROTA POST (CRIAR) - PARA O BOTÃO SALVAR (NOVO)
@admin_treinamento_bp.route('/treinamentos', methods=['POST'])
@admin_required
def criar_treinamento():
    dados = request.get_json()
    try:
        TreinamentoCreateSchema(**dados)  # Apenas para validação

        novo_treinamento = Treinamento(
            nome=dados.get('nome'),
            codigo=dados.get('codigo'),
            carga_horaria=dados.get('carga_horaria'),
            max_alunos=dados.get('max_alunos')
        )
        db.session.add(novo_treinamento)

        # Adiciona material didático se houver
        if dados.get('materiais'):
            for mat in dados['materiais']:
                if mat.get('url'):
                    novo_material = MaterialDidatico(
                        descricao=mat.get('descricao', 'Material Principal'),
                        url=mat.get('url'),
                        treinamento=novo_treinamento
                    )
                    db.session.add(novo_material)

        db.session.commit()
        return jsonify(novo_treinamento.to_dict_full()), 201
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"erro": "Erro interno ao criar treinamento"}), 500

# ROTA PUT (ATUALIZAR) - PARA O BOTÃO SALVAR (EDITAR)
@admin_treinamento_bp.route('/treinamentos/<int:id>', methods=['PUT'])
@admin_required
def atualizar_treinamento(id):
    treinamento = Treinamento.query.get_or_404(id)
    dados = request.get_json()

    treinamento.nome = dados.get('nome', treinamento.nome)
    treinamento.codigo = dados.get('codigo', treinamento.codigo)
    treinamento.carga_horaria = dados.get('carga_horaria', treinamento.carga_horaria)
    treinamento.max_alunos = dados.get('max_alunos', treinamento.max_alunos)

    # Lógica para atualizar material (simplificada)
    if dados.get('materiais'):
        MaterialDidatico.query.filter_by(treinamento_id=id).delete()
        for mat in dados['materiais']:
            if mat.get('url'):
                novo_material = MaterialDidatico(
                    descricao=mat.get('descricao', 'Material Principal'),
                    url=mat.get('url'),
                    treinamento_id=id
                )
                db.session.add(novo_material)

    db.session.commit()
    return jsonify(treinamento.to_dict_full()), 200

# ROTA DELETE (EXCLUIR) - PARA O BOTÃO EXCLUIR
@admin_treinamento_bp.route('/treinamentos/<int:id>', methods=['DELETE'])
@admin_required
def excluir_treinamento(id):
    treinamento = Treinamento.query.get_or_404(id)
    db.session.delete(treinamento)
    db.session.commit()
    return jsonify({"mensagem": "Treinamento excluído com sucesso"}), 200
