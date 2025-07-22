"""Rotas para gerenciamento de treinamentos e inscricoes."""
from flask import Blueprint, request, jsonify, g
from sqlalchemy.exc import SQLAlchemyError

from src.models import db, Treinamento, TurmaTreinamento, InscricaoTreinamento
from src.utils.error_handler import handle_internal_error
from src.schemas.treinamento import InscricaoTreinamentoCreateSchema
from src.auth import login_required


treinamento_bp = Blueprint('treinamento', __name__)


@treinamento_bp.route('/treinamentos', methods=['GET'])
@login_required
def listar_treinamentos():
    """Lista todas as turmas de treinamento."""
    turmas = (
        TurmaTreinamento.query
        .join(Treinamento)
        .order_by(Treinamento.nome)
        .all()
    )
    dados = []
    for turma in turmas:
        dados.append({
            'turma_id': turma.id,
            'treinamento': turma.treinamento.to_dict(),
            'data_inicio': turma.data_inicio.isoformat() if turma.data_inicio else None,
            'data_termino': turma.data_termino.isoformat() if turma.data_termino else None,
            'data_treinamento_pratico': turma.data_treinamento_pratico.isoformat() if turma.data_treinamento_pratico else None,
        })
    return jsonify(dados)


@treinamento_bp.route('/treinamentos/<int:turma_id>/inscricoes', methods=['POST'])
@login_required
def inscrever_usuario(turma_id):
    """Realiza a inscricao do usuario logado em uma turma."""
    turma = db.session.get(TurmaTreinamento, turma_id)
    if not turma:
        return jsonify({'erro': 'Turma não encontrada'}), 404

    existente = InscricaoTreinamento.query.filter_by(
        usuario_id=g.current_user.id,
        turma_id=turma_id
    ).first()
    if existente:
        return jsonify({'erro': 'Usuário já inscrito nesta turma'}), 400

    data = request.json or {}
    try:
        payload = InscricaoTreinamentoCreateSchema(**data)
    except Exception as e:  # pylint: disable=broad-except
        return jsonify({'erro': str(e)}), 400

    try:
        insc = InscricaoTreinamento(
            usuario_id=g.current_user.id,
            turma_id=turma_id,
            nome=payload.nome,
            email=payload.email,
            cpf=payload.cpf,
            data_nascimento=payload.data_nascimento,
            empresa=payload.empresa,
        )
        db.session.add(insc)
        db.session.commit()
        return jsonify(insc.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/treinamentos/minhas', methods=['GET'])
@login_required
def listar_meus_cursos():
    """Lista cursos em que o usuario esta inscrito."""
    inscricoes = (
        InscricaoTreinamento.query
        .filter_by(usuario_id=g.current_user.id)
        .join(TurmaTreinamento)
        .join(Treinamento)
        .all()
    )
    result = []
    for inc in inscricoes:
        result.append({
            'id': inc.id,
            'turma_id': inc.turma_id,
            'treinamento': inc.turma.treinamento.to_dict(),
            'data_inicio': inc.turma.data_inicio.isoformat() if inc.turma.data_inicio else None,
            'data_termino': inc.turma.data_termino.isoformat() if inc.turma.data_termino else None,
        })
    return jsonify(result)
