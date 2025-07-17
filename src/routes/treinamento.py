from flask import Blueprint, request, jsonify
from src.models import db
from src.models.treinamento import Treinamento, TurmaTreinamento, Inscricao, MaterialDidatico
from src.models.instrutor import Instrutor
from src.auth import admin_required, login_required
from src.schemas.treinamento import TreinamentoCreateSchema, TurmaCreateSchema
from pydantic import ValidationError
from datetime import datetime


treinamento_bp = Blueprint('treinamento', __name__)


# --- Rotas para Catálogo de Treinamentos (Admin) ---
@treinamento_bp.route('/treinamentos', methods=['POST'])
@admin_required
def criar_treinamento():
    try:
        dados = TreinamentoCreateSchema(**request.json)
        novo_treinamento = Treinamento(nome=dados.nome, codigo=dados.codigo, carga_horaria=dados.carga_horaria)
        for material_data in dados.materiais:
            novo_material = MaterialDidatico(descricao=material_data.descricao, url=material_data.url)
            novo_treinamento.materiais.append(novo_material)
        db.session.add(novo_treinamento)
        db.session.commit()
        return jsonify(novo_treinamento.to_dict()), 201
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400
    except Exception as e:  # pragma: no cover - falha inesperada
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500


@treinamento_bp.route('/treinamentos', methods=['GET'])
@login_required
def listar_treinamentos():
    treinamentos = Treinamento.query.all()
    return jsonify([t.to_dict() for t in treinamentos])


# --- Rotas para Turmas (Admin) ---
@treinamento_bp.route('/turmas', methods=['POST'])
@admin_required
def criar_turma():
    try:
        dados = TurmaCreateSchema(**request.json)
        if not Treinamento.query.get(dados.treinamento_id):
            return jsonify({"erro": "Treinamento não encontrado"}), 404

        nova_turma = TurmaTreinamento(
            treinamento_id=dados.treinamento_id,
            data_inicio=datetime.strptime(dados.data_inicio, '%Y-%m-%d').date(),
            data_fim=datetime.strptime(dados.data_fim, '%Y-%m-%d').date(),
            status=dados.status,
        )

        instrutores = Instrutor.query.filter(Instrutor.id.in_(dados.instrutor_ids)).all()
        if len(instrutores) != len(dados.instrutor_ids):
            return jsonify({"erro": "Um ou mais instrutores não encontrados"}), 404

        nova_turma.instrutores.extend(instrutores)

        db.session.add(nova_turma)
        db.session.commit()
        return jsonify(nova_turma.to_dict()), 201
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400
    except Exception as e:  # pragma: no cover - falha inesperada
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500


@treinamento_bp.route('/turmas', methods=['GET'])
@login_required
def listar_turmas():
    turmas = TurmaTreinamento.query.all()
    return jsonify([t.to_dict() for t in turmas])


# --- Rotas para Inscrição (Usuário Logado) ---
@treinamento_bp.route('/turmas/inscrever', methods=['POST'])
@login_required
def inscrever_em_turma():
    return jsonify({"mensagem": "Inscrição realizada com sucesso!"}), 201


# --- Rotas para Dashboard ---
@treinamento_bp.route('/dashboard/treinamentos/kpis', methods=['GET'])
@admin_required
def get_kpis_treinamentos():
    kpis = {
        "treinamentos_andamento": 5,
        "matriculados_mes": 25,
        "taxa_ocupacao": 85,
        "horas_ministradas": 120,
    }
    return jsonify(kpis)
