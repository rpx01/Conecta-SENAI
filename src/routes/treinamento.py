"""Rotas para gerenciamento de treinamentos e inscricoes."""

from flask import Blueprint, request, jsonify, g
from sqlalchemy.exc import SQLAlchemyError

from src.models import db, Treinamento, TurmaTreinamento, InscricaoTreinamento
from src.utils.error_handler import handle_internal_error
from src.schemas.treinamento import (
    InscricaoTreinamentoCreateSchema,
    TreinamentoCreateSchema,
    TreinamentoUpdateSchema,
    TurmaTreinamentoCreateSchema,
    TurmaTreinamentoUpdateSchema,
)
from src.auth import login_required, admin_required
from pydantic import ValidationError
from io import StringIO, BytesIO
import csv
from flask import send_file, make_response
from openpyxl import Workbook


treinamento_bp = Blueprint("treinamento", __name__)


@treinamento_bp.route("/treinamentos", methods=["GET"])
@login_required
def listar_treinamentos():
    """Lista todas as turmas de treinamento."""
    turmas = TurmaTreinamento.query.join(Treinamento).order_by(Treinamento.nome).all()
    dados = []
    for turma in turmas:
        dados.append(
            {
                "turma_id": turma.id,
                "treinamento": turma.treinamento.to_dict(),
                "data_inicio": (
                    turma.data_inicio.isoformat() if turma.data_inicio else None
                ),
                "data_fim": (
                    turma.data_fim.isoformat() if turma.data_fim else None
                ),
                "data_treinamento_pratico": (
                    turma.data_treinamento_pratico.isoformat()
                    if turma.data_treinamento_pratico
                    else None
                ),
            }
        )
    return jsonify(dados)


@treinamento_bp.route("/treinamentos/<int:turma_id>/inscricoes", methods=["POST"])
@login_required
def inscrever_usuario(turma_id):
    """Realiza a inscricao do usuario logado em uma turma."""
    turma = db.session.get(TurmaTreinamento, turma_id)
    if not turma:
        return jsonify({"erro": "Turma não encontrada"}), 404

    existente = InscricaoTreinamento.query.filter_by(
        usuario_id=g.current_user.id, turma_id=turma_id
    ).first()
    if existente:
        return jsonify({"erro": "Usuário já inscrito nesta turma"}), 400

    data = request.json or {}
    try:
        payload = InscricaoTreinamentoCreateSchema(**data)
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

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


@treinamento_bp.route("/treinamentos/minhas", methods=["GET"])
@login_required
def listar_meus_cursos():
    """Lista cursos em que o usuario esta inscrito."""
    inscricoes = (
        InscricaoTreinamento.query.filter_by(usuario_id=g.current_user.id)
        .join(TurmaTreinamento)
        .join(Treinamento)
        .all()
    )
    result = []
    for inc in inscricoes:
        result.append(
            {
                "id": inc.id,
                "turma_id": inc.turma_id,
                "treinamento": inc.turma.treinamento.to_dict(),
                "data_inicio": (
                    inc.turma.data_inicio.isoformat() if inc.turma.data_inicio else None
                ),
                "data_fim": (
                    inc.turma.data_fim.isoformat()
                    if inc.turma.data_fim
                    else None
                ),
            }
        )
    return jsonify(result)


@treinamento_bp.route("/treinamentos/catalogo", methods=["GET"])
@login_required
def listar_catalogo_treinamentos():
    """Lista os treinamentos cadastrados."""
    treins = Treinamento.query.order_by(Treinamento.nome).all()
    return jsonify([t.to_dict() for t in treins])


@treinamento_bp.route("/treinamentos/catalogo", methods=["POST"])
@admin_required
def criar_treinamento():
    """Cadastra um novo treinamento."""
    data = request.json or {}
    try:
        payload = TreinamentoCreateSchema(**data)
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400

    # Verifica se já existe um treinamento com o mesmo nome e código
    if Treinamento.query.filter_by(nome=payload.nome, codigo=payload.codigo).first():
        return jsonify({"erro": "Já existe um treinamento com este nome e código"}), 400
    # Código continua único para evitar duplicidade
    if Treinamento.query.filter_by(codigo=payload.codigo).first():
        return jsonify({"erro": "Já existe um treinamento com este código"}), 400
    try:
        novo = Treinamento(
            nome=payload.nome,
            codigo=payload.codigo,
            capacidade_maxima=payload.capacidade_maxima,
            carga_horaria=payload.carga_horaria,
            tem_pratica=payload.tem_pratica,
            links_materiais=payload.links_materiais,
            tipo=payload.tipo,
            conteudo_programatico=payload.conteudo_programatico
        )
        db.session.add(novo)
        db.session.commit()
        return jsonify(novo.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route("/treinamentos/catalogo/<int:treinamento_id>", methods=["GET"])
@login_required
def obter_treinamento(treinamento_id):
    """Obtém um treinamento específico."""
    treino = db.session.get(Treinamento, treinamento_id)
    if not treino:
        return jsonify({"erro": "Treinamento não encontrado"}), 404
    return jsonify(treino.to_dict())


@treinamento_bp.route("/treinamentos/catalogo/<int:treinamento_id>", methods=["PUT"])
@admin_required
def atualizar_treinamento(treinamento_id):
    """Atualiza um treinamento existente."""
    treino = db.session.get(Treinamento, treinamento_id)
    if not treino:
        return jsonify({"erro": "Treinamento não encontrado"}), 404
    data = request.json or {}
    try:
        payload = TreinamentoUpdateSchema(**data)
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400

    novo_nome = payload.nome if payload.nome is not None else treino.nome
    novo_codigo = payload.codigo if payload.codigo is not None else treino.codigo

    existente = Treinamento.query.filter_by(nome=novo_nome, codigo=novo_codigo).first()
    if existente and existente.id != treinamento_id:
        return jsonify({"erro": "Já existe um treinamento com este nome e código"}), 400

    if payload.nome is not None:
        treino.nome = payload.nome
    if payload.codigo is not None:
        existente_codigo = Treinamento.query.filter_by(codigo=payload.codigo).first()
        if existente_codigo and existente_codigo.id != treinamento_id:
            return jsonify({"erro": "Já existe um treinamento com este código"}), 400
        treino.codigo = payload.codigo
    if payload.capacidade_maxima is not None:
        treino.capacidade_maxima = payload.capacidade_maxima
    if payload.carga_horaria is not None:
        treino.carga_horaria = payload.carga_horaria
    if payload.tem_pratica is not None:
        treino.tem_pratica = payload.tem_pratica
    if payload.links_materiais is not None:
        treino.links_materiais = payload.links_materiais
    if payload.tipo is not None:
        treino.tipo = payload.tipo
    if payload.conteudo_programatico is not None:
        treino.conteudo_programatico = payload.conteudo_programatico
        
    try:
        db.session.commit()
        return jsonify(treino.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route("/treinamentos/catalogo/<int:treinamento_id>", methods=["DELETE"])
@admin_required
def remover_treinamento(treinamento_id):
    """Exclui um treinamento."""
    treino = db.session.get(Treinamento, treinamento_id)
    if not treino:
        return jsonify({"erro": "Treinamento não encontrado"}), 404
    try:
        db.session.delete(treino)
        db.session.commit()
        return jsonify({"mensagem": "Treinamento removido com sucesso"})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route("/treinamentos/turmas", methods=["POST"])
@admin_required
def criar_turma_treinamento():
    """Cria uma turma para um treinamento."""
    data = request.json or {}
    try:
        payload = TurmaTreinamentoCreateSchema(**data)
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400

    if not db.session.get(Treinamento, payload.treinamento_id):
        return jsonify({"erro": "Treinamento não encontrado"}), 404
    turma = TurmaTreinamento(
        treinamento_id=payload.treinamento_id,
        data_inicio=payload.data_inicio,
        data_fim=payload.data_fim,
        data_treinamento_pratico=payload.data_treinamento_pratico,
    )
    try:
        db.session.add(turma)
        db.session.commit()
        return jsonify(turma.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route("/treinamentos/turmas/<int:turma_id>", methods=["PUT"])
@admin_required
def atualizar_turma_treinamento(turma_id):
    """Atualiza uma turma."""
    turma = db.session.get(TurmaTreinamento, turma_id)
    if not turma:
        return jsonify({"erro": "Turma não encontrada"}), 404
    data = request.json or {}
    try:
        payload = TurmaTreinamentoUpdateSchema(**data)
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400

    if payload.treinamento_id is not None:
        if not db.session.get(Treinamento, payload.treinamento_id):
            return jsonify({"erro": "Treinamento não encontrado"}), 404
        turma.treinamento_id = payload.treinamento_id
    if payload.data_inicio is not None:
        turma.data_inicio = payload.data_inicio
    if payload.data_fim is not None:
        turma.data_fim = payload.data_fim
    if payload.data_treinamento_pratico is not None:
        turma.data_treinamento_pratico = payload.data_treinamento_pratico
    try:
        db.session.commit()
        return jsonify(turma.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route("/treinamentos/turmas/<int:turma_id>", methods=["DELETE"])
@admin_required
def remover_turma_treinamento(turma_id):
    """Remove uma turma."""
    turma = db.session.get(TurmaTreinamento, turma_id)
    if not turma:
        return jsonify({"erro": "Turma não encontrada"}), 404
    try:
        db.session.delete(turma)
        db.session.commit()
        return jsonify({"mensagem": "Turma removida com sucesso"})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route("/treinamentos/turmas/<int:turma_id>/inscricoes", methods=["GET"])
@admin_required
def listar_inscricoes(turma_id):
    """Lista inscrições de uma turma."""
    turma = db.session.get(TurmaTreinamento, turma_id)
    if not turma:
        return jsonify({"erro": "Turma não encontrada"}), 404
    inscricoes = InscricaoTreinamento.query.filter_by(turma_id=turma_id).all()
    return jsonify([i.to_dict() for i in inscricoes])


@treinamento_bp.route(
    "/treinamentos/turmas/<int:turma_id>/inscricoes/admin", methods=["POST"]
)
@admin_required
def criar_inscricao_admin(turma_id):
    """Adiciona manualmente uma inscrição em uma turma."""
    if not db.session.get(TurmaTreinamento, turma_id):
        return jsonify({"erro": "Turma não encontrada"}), 404
    data = request.json or {}
    try:
        payload = InscricaoTreinamentoCreateSchema(**data)
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400
    insc = InscricaoTreinamento(
        usuario_id=None,
        turma_id=turma_id,
        nome=payload.nome,
        email=payload.email,
        cpf=payload.cpf,
        data_nascimento=payload.data_nascimento,
        empresa=payload.empresa,
    )
    try:
        db.session.add(insc)
        db.session.commit()
        return jsonify(insc.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@treinamento_bp.route(
    "/treinamentos/turmas/<int:turma_id>/inscricoes/export", methods=["GET"]
)
@admin_required
def exportar_inscricoes(turma_id):
    """Exporta inscrições de uma turma em CSV ou XLSX."""
    turma = db.session.get(TurmaTreinamento, turma_id)
    if not turma:
        return jsonify({"erro": "Turma não encontrada"}), 404
    formato = request.args.get("formato", "csv").lower()
    inscricoes = InscricaoTreinamento.query.filter_by(turma_id=turma_id).all()

    if formato == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.append(["ID", "Nome", "Email", "CPF"])
        for i in inscricoes:
            ws.append([i.id, i.nome, i.email, i.cpf])
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        return send_file(
            buf,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="inscricoes.xlsx",
        )

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID", "Nome", "Email", "CPF"])
    for i in inscricoes:
        writer.writerow([i.id, i.nome, i.email, i.cpf])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=inscricoes.csv"
    output.headers["Content-Type"] = "text/csv"
    return output
