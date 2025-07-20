from flask import Blueprint, request, jsonify, g
from src.models import db
from src.models.treinamento import (
    Treinamento,
    TurmaTreinamento,
    Inscricao,
    MaterialDidatico,
)
from src.models.instrutor import Instrutor
from src.models.user import User
from src.auth import admin_required, login_required
from datetime import datetime


treinamento_bp = Blueprint('treinamento', __name__)


@treinamento_bp.route('/catalogo', methods=['GET'])
def catalogo_publico():
    """Retorna lista simplificada de treinamentos."""
    treinamentos = Treinamento.query.with_entities(
        Treinamento.id,
        Treinamento.nome,
        Treinamento.codigo,
        Treinamento.carga_horaria,
    ).order_by(Treinamento.nome).all()
    return jsonify([
        {
            'id': t.id,
            'nome': t.nome,
            'codigo': t.codigo,
            'carga_horaria': t.carga_horaria,
        }
        for t in treinamentos
    ])


@treinamento_bp.route('/treinamentos', methods=['GET'])
def listar_treinamentos():
    treinamentos = Treinamento.query.order_by(Treinamento.nome).all()
    return jsonify([t.to_dict() for t in treinamentos])


@treinamento_bp.route('/treinamentos/<int:id>', methods=['GET'])
@login_required
def obter_treinamento(id):
    treinamento = db.session.get(Treinamento, id)
    if not treinamento:
        return jsonify({'erro': 'Treinamento não encontrado'}), 404
    return jsonify(treinamento.to_dict())


@treinamento_bp.route('/treinamentos', methods=['POST'])
@admin_required
def criar_treinamento():
    data = request.json or {}
    nome = (data.get('nome') or '').strip()
    carga_horaria = data.get('carga_horaria')
    max_alunos = data.get('max_alunos')
    codigo = (data.get('codigo') or '').strip() or None
    materiais = (data.get('materiais') or '').strip() or None

    if not nome or carga_horaria is None or max_alunos is None:
        return jsonify({'erro': "Campos 'nome', 'carga_horaria' e 'max_alunos' são obrigatórios."}), 400

    try:
        carga_horaria = int(carga_horaria)
        max_alunos = int(max_alunos)
    except (TypeError, ValueError):
        return jsonify({'erro': 'carga_horaria e max_alunos devem ser inteiros'}), 400

    if carga_horaria <= 0 or max_alunos <= 0:
        return jsonify({'erro': 'Valores devem ser positivos'}), 400

    if Treinamento.query.filter_by(nome=nome).first():
        return jsonify({'erro': 'Treinamento já existe'}), 400

    if codigo and Treinamento.query.filter_by(codigo=codigo).first():
        return jsonify({'erro': 'Já existe um treinamento com este código'}), 400

    novo = Treinamento(
        nome=nome,
        codigo=codigo,
        carga_horaria=carga_horaria,
        max_alunos=max_alunos,
        materiais=materiais,
    )
    db.session.add(novo)
    db.session.commit()
    return jsonify(novo.to_dict()), 201


@treinamento_bp.route('/treinamentos/<int:id>', methods=['PUT'])
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
        try:
            treinamento.max_alunos = int(data.get('max_alunos'))
        except (TypeError, ValueError):
            return jsonify({'erro': 'max_alunos deve ser inteiro'}), 400

    if 'materiais' in data:
        treinamento.materiais = (data.get('materiais') or '').strip() or None

    db.session.commit()
    return jsonify(treinamento.to_dict())


@treinamento_bp.route('/treinamentos/<int:id>', methods=['DELETE'])
@admin_required
def remover_treinamento(id):
    treinamento = db.session.get(Treinamento, id)
    if not treinamento:
        return jsonify({'erro': 'Treinamento não encontrado'}), 404
    db.session.delete(treinamento)
    db.session.commit()
    return jsonify({'mensagem': 'Treinamento removido'})


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


@treinamento_bp.route('/turmas', methods=['GET'])
@login_required
def listar_turmas():
    turmas = TurmaTreinamento.query.order_by(TurmaTreinamento.data_inicio).all()
    return jsonify([t.to_dict() for t in turmas])


@treinamento_bp.route('/turmas/<int:id>', methods=['GET'])
@login_required
def obter_turma(id):
    turma = db.session.get(TurmaTreinamento, id)
    if not turma:
        return jsonify({'erro': 'Turma não encontrada'}), 404
    return jsonify(turma.to_dict())


@treinamento_bp.route('/turmas', methods=['POST'])
@admin_required
def criar_turma():
    data = request.json or {}
    treinamento_id = data.get('treinamento_id')
    data_inicio = data.get('data_inicio')
    data_fim = data.get('data_fim')
    instrutores = data.get('instrutores', [])

    if not treinamento_id or not data_inicio or not data_fim:
        return jsonify({'erro': 'treinamento_id, data_inicio e data_fim são obrigatórios'}), 400

    turma = TurmaTreinamento(
        treinamento_id=treinamento_id,
        data_inicio=datetime.fromisoformat(data_inicio).date(),
        data_fim=datetime.fromisoformat(data_fim).date(),
    )

    for inst_id in instrutores:
        instrutor = db.session.get(Instrutor, inst_id)
        if instrutor:
            turma.instrutores.append(instrutor)

    db.session.add(turma)
    db.session.commit()
    return jsonify(turma.to_dict()), 201


@treinamento_bp.route('/turmas/<int:id>', methods=['PUT'])
@admin_required
def atualizar_turma(id):
    turma = db.session.get(TurmaTreinamento, id)
    if not turma:
        return jsonify({'erro': 'Turma não encontrada'}), 404

    data = request.json or {}

    if 'data_inicio' in data:
        turma.data_inicio = datetime.fromisoformat(data['data_inicio']).date()

    if 'data_fim' in data:
        turma.data_fim = datetime.fromisoformat(data['data_fim']).date()

    if 'status' in data:
        turma.status = data['status']

    if 'instrutores' in data:
        turma.instrutores.clear()
        for inst_id in data['instrutores']:
            instrutor = db.session.get(Instrutor, inst_id)
            if instrutor:
                turma.instrutores.append(instrutor)

    db.session.commit()
    return jsonify(turma.to_dict())


@treinamento_bp.route('/turmas/<int:id>', methods=['DELETE'])
@admin_required
def remover_turma(id):
    turma = db.session.get(TurmaTreinamento, id)
    if not turma:
        return jsonify({'erro': 'Turma não encontrada'}), 404
    db.session.delete(turma)
    db.session.commit()
    return jsonify({'mensagem': 'Turma removida'})


@treinamento_bp.route('/dashboard/kpis', methods=['GET'])
@login_required
def obter_kpis():
    total_treinamentos = Treinamento.query.count()
    total_turmas = TurmaTreinamento.query.count()
    total_inscricoes = Inscricao.query.count()
    turmas_ativas = TurmaTreinamento.query.filter(
        TurmaTreinamento.status.in_(['A realizar', 'Em andamento'])
    ).count()

    return jsonify({
        'total_treinamentos': total_treinamentos,
        'total_turmas': total_turmas,
        'total_inscricoes': total_inscricoes,
        'turmas_ativas': turmas_ativas,
    })
