"""Rotas para gerenciamento de treinamentos e turmas."""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

from src.models import db
from src.models.treinamento import Treinamento
from src.models.turma import TurmaTreinamento
from src.models.participacao import Inscricao, Presenca
from src.routes.user import verificar_autenticacao, verificar_admin
from src.utils.error_handler import handle_internal_error


treinamento_bp = Blueprint('treinamento', __name__)


@treinamento_bp.route('/treinamentos/catalogo', methods=['GET'])
def catalogo_treinamentos():
    """Retorna o catálogo de treinamentos."""
    treinamentos = Treinamento.query.order_by(Treinamento.nome).all()
    return jsonify([t.to_dict() for t in treinamentos])


@treinamento_bp.route('/turmas/<int:id>/inscrever', methods=['POST'])
def inscrever(id):
    """Inscreve o usuário logado em uma turma."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    turma = db.session.get(TurmaTreinamento, id)
    if not turma:
        return jsonify({'erro': 'Turma não encontrada'}), 404

    if Inscricao.query.filter_by(turma_id=id, usuario_id=user.id).first():
        return jsonify({'erro': 'Usuário já inscrito'}), 400

    try:
        insc = Inscricao(turma_id=id, usuario_id=user.id)
        db.session.add(insc)
        db.session.commit()
        return jsonify(insc.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/meus-treinamentos', methods=['GET'])
def meus_treinamentos():
    """Lista as turmas em que o usuário está inscrito."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    inscricoes = Inscricao.query.filter_by(usuario_id=user.id).all()
    return jsonify([i.turma.to_dict() for i in inscricoes])


# ----- Rotas Admin -----


def _verifica_admin(request):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return None, jsonify({'erro': 'Não autenticado'}), 401
    if not verificar_admin(user):
        return None, jsonify({'erro': 'Permissão negada'}), 403
    return user, None, None


@treinamento_bp.route('/admin/treinamentos', methods=['GET', 'POST'])
def admin_treinamentos():
    user, resp, code = _verifica_admin(request)
    if resp:
        return resp, code

    if request.method == 'GET':
        treinamentos = Treinamento.query.order_by(Treinamento.nome).all()
        return jsonify([t.to_dict() for t in treinamentos])

    data = request.json or {}
    nome = (data.get('nome') or '').strip()
    codigo = data.get('codigo')
    carga_horaria = data.get('carga_horaria')

    if not nome or carga_horaria is None:
        return jsonify({'erro': 'Dados incompletos'}), 400

    try:
        novo = Treinamento(nome=nome, codigo=codigo, carga_horaria=carga_horaria)
        db.session.add(novo)
        db.session.commit()
        return jsonify(novo.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/admin/treinamentos/<int:id>', methods=['PUT', 'DELETE'])
def admin_treinamento_id(id):
    user, resp, code = _verifica_admin(request)
    if resp:
        return resp, code

    treinamento = db.session.get(Treinamento, id)
    if not treinamento:
        return jsonify({'erro': 'Treinamento não encontrado'}), 404

    if request.method == 'DELETE':
        try:
            db.session.delete(treinamento)
            db.session.commit()
            return jsonify({'mensagem': 'Treinamento removido'})
        except SQLAlchemyError as e:
            db.session.rollback()
            return handle_internal_error(e)

    data = request.json or {}
    treinamento.nome = (data.get('nome') or treinamento.nome).strip()
    treinamento.codigo = data.get('codigo', treinamento.codigo)
    treinamento.carga_horaria = data.get('carga_horaria', treinamento.carga_horaria)
    try:
        db.session.commit()
        return jsonify(treinamento.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/admin/turmas', methods=['GET', 'POST'])
def admin_turmas():
    user, resp, code = _verifica_admin(request)
    if resp:
        return resp, code

    if request.method == 'GET':
        turmas = TurmaTreinamento.query.order_by(TurmaTreinamento.data_inicio).all()
        return jsonify([t.to_dict() for t in turmas])

    data = request.json or {}
    treinamento_id = data.get('treinamento_id')
    data_inicio = data.get('data_inicio')
    data_fim = data.get('data_fim')
    status = data.get('status') or 'A realizar'

    if not all([treinamento_id, data_inicio, data_fim]):
        return jsonify({'erro': 'Dados incompletos'}), 400

    try:
        inicio = datetime.fromisoformat(data_inicio)
        fim = datetime.fromisoformat(data_fim)
    except ValueError:
        return jsonify({'erro': 'Datas inválidas'}), 400

    try:
        turma = TurmaTreinamento(
            treinamento_id=treinamento_id,
            data_inicio=inicio,
            data_fim=fim,
            status=status,
        )
        db.session.add(turma)
        db.session.commit()
        return jsonify(turma.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/admin/turmas/<int:id>', methods=['PUT', 'DELETE'])
def admin_turma_id(id):
    user, resp, code = _verifica_admin(request)
    if resp:
        return resp, code

    turma = db.session.get(TurmaTreinamento, id)
    if not turma:
        return jsonify({'erro': 'Turma não encontrada'}), 404

    if request.method == 'DELETE':
        try:
            db.session.delete(turma)
            db.session.commit()
            return jsonify({'mensagem': 'Turma removida'})
        except SQLAlchemyError as e:
            db.session.rollback()
            return handle_internal_error(e)

    data = request.json or {}
    if 'treinamento_id' in data:
        turma.treinamento_id = data['treinamento_id']
    if 'data_inicio' in data:
        try:
            turma.data_inicio = datetime.fromisoformat(data['data_inicio'])
        except ValueError:
            return jsonify({'erro': 'Data início inválida'}), 400
    if 'data_fim' in data:
        try:
            turma.data_fim = datetime.fromisoformat(data['data_fim'])
        except ValueError:
            return jsonify({'erro': 'Data fim inválida'}), 400
    if 'status' in data:
        turma.status = data['status']

    try:
        db.session.commit()
        return jsonify(turma.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/admin/turmas/<int:id>/participantes', methods=['GET'])
def participantes_turma(id):
    user, resp, code = _verifica_admin(request)
    if resp:
        return resp, code

    turma = db.session.get(TurmaTreinamento, id)
    if not turma:
        return jsonify({'erro': 'Turma não encontrada'}), 404

    inscritos = [i.usuario.to_dict() for i in turma.inscricoes]
    return jsonify(inscritos)


@treinamento_bp.route('/admin/presenca', methods=['POST'])
def registrar_presenca():
    user, resp, code = _verifica_admin(request)
    if resp:
        return resp, code

    data = request.json or {}
    inscricao_id = data.get('inscricao_id')
    data_presenca = data.get('data')
    presente = bool(data.get('presente'))

    if not all([inscricao_id, data_presenca]):
        return jsonify({'erro': 'Dados incompletos'}), 400

    inscricao = db.session.get(Inscricao, inscricao_id)
    if not inscricao:
        return jsonify({'erro': 'Inscrição não encontrada'}), 404

    try:
        dia = datetime.fromisoformat(data_presenca).date()
    except ValueError:
        return jsonify({'erro': 'Data inválida'}), 400

    try:
        presenca = Presenca(
            inscricao_id=inscricao_id,
            data=dia,
            presente=presente,
        )
        db.session.add(presenca)
        db.session.commit()
        return jsonify(presenca.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route('/admin/dashboard/treinamentos', methods=['GET'])
def dashboard_treinamentos():
    user, resp, code = _verifica_admin(request)
    if resp:
        return resp, code

    em_andamento = TurmaTreinamento.query.filter(TurmaTreinamento.status == 'Em andamento').count()

    now = datetime.utcnow()
    inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if inicio_mes.month == 12:
        proximo_mes = inicio_mes.replace(year=inicio_mes.year + 1, month=1)
    else:
        proximo_mes = inicio_mes.replace(month=inicio_mes.month + 1)

    participantes_mes = (
        db.session.query(func.count(Inscricao.id))
        .join(TurmaTreinamento, Inscricao.turma_id == TurmaTreinamento.id)
        .filter(TurmaTreinamento.data_inicio >= inicio_mes, TurmaTreinamento.data_inicio < proximo_mes)
        .scalar()
    )

    mais_procurados = (
        db.session.query(Treinamento.nome, func.count(Inscricao.id).label('total'))
        .join(TurmaTreinamento, TurmaTreinamento.treinamento_id == Treinamento.id)
        .join(Inscricao, Inscricao.turma_id == TurmaTreinamento.id)
        .group_by(Treinamento.id)
        .order_by(func.count(Inscricao.id).desc())
        .limit(5)
        .all()
    )

    return jsonify({
        'em_andamento': em_andamento,
        'participantes_mes': participantes_mes or 0,
        'mais_procurados': [
            {'treinamento': nome, 'inscritos': total} for nome, total in mais_procurados
        ],
    })
