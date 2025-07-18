from flask import Blueprint, request, jsonify, g
from src.models import db
from src.models.treinamento import Treinamento, TurmaTreinamento, Inscricao, MaterialDidatico
from src.models.instrutor import Instrutor
from src.models.user import User
from src.auth import admin_required, login_required
from datetime import datetime


treinamento_bp = Blueprint('treinamento', __name__)


@treinamento_bp.route('/treinamentos', methods=['GET'])
@login_required
def listar_treinamentos():
    treinamentos = Treinamento.query.order_by(Treinamento.nome).all()
    return jsonify([t.to_dict() for t in treinamentos])


@treinamento_bp.route('/turmas_disponiveis', methods=['GET'])
@login_required
def listar_turmas_disponiveis():
    turmas = TurmaTreinamento.query.filter(TurmaTreinamento.status.in_(['A realizar', 'Em andamento'])).all()
    return jsonify([t.to_dict() for t in turmas])


@treinamento_bp.route('/turmas/inscrever', methods=['POST'])
@login_required
def inscrever_em_turma():
    user = g.current_user
    data = request.get_json()
    turma_id = data.get('turma_id') if data else None

    if not turma_id:
        return jsonify({"erro": "ID da turma é obrigatório"}), 400

    turma = TurmaTreinamento.query.get(turma_id)
    if not turma:
        return jsonify({"erro": "Turma não encontrada"}), 404

    ja_inscrito = Inscricao.query.filter_by(turma_id=turma_id, usuario_id=user.id).first()
    if ja_inscrito:
        return jsonify({"erro": "Você já está inscrito nesta turma"}), 409

    nova_inscricao = Inscricao(turma_id=turma_id, usuario_id=user.id)
    db.session.add(nova_inscricao)
    db.session.commit()

    return jsonify({"mensagem": "Inscrição realizada com sucesso!"}), 201
