# flake8: noqa
"""Rotas para gerenciamento de itens do planejamento trimestral."""
from datetime import datetime, date
import hmac
from uuid import uuid4
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from conectasenai_api.models import db, EmailSecretaria
from conectasenai_api.models.planejamento import (
    PlanejamentoItem,
    Horario,
    CargaHoraria,
    Modalidade,
    PlanejamentoTreinamento,
    Local,
    PublicoAlvo,
)
from conectasenai_api.models.treinamento import Treinamento
from conectasenai_api.models.instrutor import Instrutor
from conectasenai_api.routes.user import verificar_autenticacao
from conectasenai_api.utils.error_handler import handle_internal_error
from pydantic import ValidationError
from conectasenai_api.schemas.planejamento import PlanejamentoCreateSchema
from conectasenai_api.services import email_service

planejamento_bp = Blueprint('planejamento', __name__)


@planejamento_bp.before_request
def verificar_csrf():
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        token_cookie = request.cookies.get("csrf_token")
        token_header = request.headers.get("X-CSRF-Token") or request.headers.get("X-CSRFToken")
        if not token_cookie or not token_header or not hmac.compare_digest(token_cookie, token_header):
            return jsonify({"erro": "CSRF token inválido"}), 403


def _tabela_planejamento_existe() -> bool:
    """Garantia de existência da tabela e colunas necessárias."""
    tabela = PlanejamentoItem.__tablename__
    insp = inspect(db.engine)

    if not insp.has_table(tabela):
        try:
            PlanejamentoItem.__table__.create(db.engine)
            insp = inspect(db.engine)
        except SQLAlchemyError:
            return False

    colunas = {col["name"] for col in insp.get_columns(tabela)}
    try:
        with db.engine.begin() as conn:
            if "sge_ativo" not in colunas:
                conn.execute(
                    text(
                        f"ALTER TABLE {tabela} "
                        "ADD COLUMN sge_ativo BOOLEAN DEFAULT FALSE"
                    )
                )
            if "sge_link" not in colunas:
                conn.execute(
                    text(
                        f"ALTER TABLE {tabela} "
                        "ADD COLUMN sge_link VARCHAR(512)"
                    )
                )
    except SQLAlchemyError:
        return False

    return True


@planejamento_bp.route('/planejamento', methods=['GET'])
def listar_planejamentos():
    """Lista todos os itens de planejamento."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    try:
        if not _tabela_planejamento_existe():
            return jsonify([]), 200

        itens = PlanejamentoItem.query.all()

        # Mapeia os horários pelo nome para evitar consultas repetidas.
        horarios = {h.nome: h for h in Horario.query.all()}
        out = []
        for item in itens:
            data = item.to_dict()
            h = horarios.get(item.horario)
            if h:
                data["horario"] = {"id": h.id, "nome": h.nome, "turno": h.turno}
            else:
                data["horario"] = {"id": None, "nome": item.horario, "turno": None}
            out.append(data)

        return jsonify(out)
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@planejamento_bp.route('/planejamento/itens', methods=['GET'])
def listar_itens():
    """Lista todos os itens do planejamento (alias usado pelo frontend)."""
    return listar_planejamentos()


@planejamento_bp.route('/planejamento', methods=['POST'])
def criar_planejamento():
    """Cria um ou mais itens de planejamento."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    if not _tabela_planejamento_existe():
        return (
            jsonify({'erro': 'Tabela planejamento_itens não existe; execute as migrações.'}),
            500,
        )

    payload = request.get_json() or {}
    try:
        dados = PlanejamentoCreateSchema(**payload)
    except ValidationError as exc:
        detalhes = {err['loc'][-1]: err['msg'] for err in exc.errors()}
        return jsonify({'erro': 'Dados inválidos', 'detalhes': detalhes}), 422

    lote_id = str(uuid4())
    itens = []
    detalhes = {}

    for registro in dados.registros:
        if not Treinamento.query.filter_by(nome=registro.treinamento).first():
            detalhes.setdefault('treinamento', 'Treinamento não encontrado')
        if not Instrutor.query.filter_by(nome=registro.instrutor).first():
            detalhes.setdefault('instrutor', 'Instrutor não encontrado')

    if detalhes:
        return jsonify({'erro': 'Dados inválidos', 'detalhes': detalhes}), 422

    for registro in dados.registros:
        item = PlanejamentoItem(
            row_id=str(uuid4()),
            lote_id=lote_id,
            data=registro.inicio,
            semana=registro.semana,
            horario=registro.horario,
            carga_horaria=str(registro.carga_horaria),
            modalidade=registro.modalidade,
            treinamento=registro.treinamento,
            cmd=str(registro.polos.cmd),
            sjb=str(registro.polos.sjb),
            sag_tombos=str(registro.polos.sag_tombos),
            instrutor=registro.instrutor,
            local=registro.local,
            observacao=registro.observacao,
            sge_ativo=registro.sge_ativo,
            sge_link=registro.sge_link,
        )
        itens.append(item)

    try:
        for item in itens:
            db.session.add(item)
        db.session.commit()
        return jsonify({'mensagem': 'Planejamento salvo', 'quantidade': len(itens)}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.exception('Erro ao criar planejamento', extra={'payload': payload})
        return handle_internal_error(e)


@planejamento_bp.route('/planejamento/itens', methods=['POST'])
def criar_item():
    """Cria um único item de planejamento (utilizado pela interface web)."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    if not _tabela_planejamento_existe():
        return (
            jsonify({'erro': 'Tabela planejamento_itens não existe; execute as migrações.'}),
            500,
        )

    payload = request.get_json() or {}
    detalhes = {}

    treinamento_nome = payload.get('treinamento')
    instrutor_nome = payload.get('instrutor')

    # Os dados exibidos na interface de planejamento são carregados a partir
    # das tabelas "planejamento" (como PlanejamentoTreinamento) e nem sempre
    # correspondem aos registros reais de Treinamento. A validação anterior
    # verificava apenas na tabela de treinamentos, o que resultava em erros de
    # "Dados inválidos" ao salvar itens que existiam apenas na base de dados do
    # planejamento. Agora verificamos se o treinamento existe em qualquer uma das
    # tabelas conhecidas (Treinamento ou PlanejamentoTreinamento), permitindo que
    # o usuário cadastre itens válidos mesmo que o treinamento não esteja na
    # tabela principal de treinamentos.
    if treinamento_nome:
        treinamento_existe = (
            Treinamento.query.filter_by(nome=treinamento_nome).first()
            or PlanejamentoTreinamento.query.filter_by(nome=treinamento_nome).first()
        )
        if not treinamento_existe:
            detalhes['treinamento'] = 'Treinamento não encontrado'

    if instrutor_nome and not Instrutor.query.filter_by(nome=instrutor_nome).first():
        detalhes['instrutor'] = 'Instrutor não encontrado'

    if detalhes:
        return jsonify({'erro': 'Dados inválidos', 'detalhes': detalhes}), 422

    try:
        data_obj = datetime.fromisoformat(payload.get('data', '')).date()
    except Exception:
        return jsonify({'erro': 'Data inválida'}), 400

    item = PlanejamentoItem(
        row_id=str(uuid4()),
        lote_id=payload.get('loteId') or str(uuid4()),
        data=data_obj,
        semana=payload.get('semana'),
        horario=payload.get('horario'),
        carga_horaria=payload.get('carga_horaria'),
        modalidade=payload.get('modalidade'),
        treinamento=treinamento_nome,
        cmd=payload.get('cmd'),
        sjb=payload.get('sjb'),
        sag_tombos=payload.get('sag_tombos'),
        instrutor=instrutor_nome,
        local=payload.get('local'),
        observacao=payload.get('observacao'),
        sge_ativo=payload.get('sge_ativo', False),
        sge_link=payload.get('sge_link'),
    )

    try:
        db.session.add(item)
        db.session.commit()
        try:
            dados_do_item = item.to_dict()
            email_service.enviar_notificacao_planejamento(
                assunto="Novo Item Adicionado ao Planejamento",
                nome_template="email/novo_item_planejamento.html.j2",
                contexto={"item": dados_do_item},
            )
        except Exception as e:
            current_app.logger.error(
                f"Falha ao enviar e-mail de notificação de novo item: {e}"
            )
        return jsonify(item.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@planejamento_bp.route('/planejamentos', methods=['POST'])
def criar_planejamento_ids():
    """Cria um item de planejamento utilizando os IDs das tabelas base."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    if not _tabela_planejamento_existe():
        return (
            jsonify({'erro': 'Tabela planejamento_itens não existe; execute as migrações.'}),
            500,
        )

    payload = request.get_json() or {}

    campos_obrigatorios = [
        'data_inicial', 'data_final', 'horario_id', 'carga_horaria_id',
        'modalidade_id', 'treinamento_id', 'instrutor_id', 'local_id',
        'cmd_id', 'sjb_id', 'sag_tombos_id'
    ]
    erros = {}

    for campo in campos_obrigatorios:
        if payload.get(campo) in (None, ''):
            erros[campo] = 'Campo obrigatório'

    try:
        data_inicial = date.fromisoformat(payload.get('data_inicial', ''))
        date.fromisoformat(payload.get('data_final', ''))
    except Exception:
        erros['data'] = 'Datas inválidas'

    def obter_modelo(modelo, campo):
        valor = payload.get(campo)
        if not isinstance(valor, int):
            erros[campo] = 'Deve ser inteiro'
            return None
        obj = modelo.query.get(valor)
        if not obj:
            erros[campo] = 'Não encontrado'
        return obj

    horario = obter_modelo(Horario, 'horario_id')
    carga = obter_modelo(CargaHoraria, 'carga_horaria_id')
    modalidade = obter_modelo(Modalidade, 'modalidade_id')
    treinamento = obter_modelo(PlanejamentoTreinamento, 'treinamento_id')
    instrutor = obter_modelo(Instrutor, 'instrutor_id')
    local = obter_modelo(Local, 'local_id')
    cmd = obter_modelo(PublicoAlvo, 'cmd_id')
    sjb = obter_modelo(PublicoAlvo, 'sjb_id')
    sag = obter_modelo(PublicoAlvo, 'sag_tombos_id')

    if erros:
        return jsonify({'erro': 'Dados inválidos', 'errors': erros}), 422

    semana = None
    try:
        primeiro_dia = date(data_inicial.year, 1, 1)
        dias_passados = (data_inicial - primeiro_dia).days
        semana = f"SEMANA {((data_inicial.weekday() + 1 + dias_passados) // 7) + 1}"
    except Exception:
        semana = None

    item = PlanejamentoItem(
        row_id=str(uuid4()),
        lote_id=str(uuid4()),
        data=data_inicial,
        semana=semana,
        horario=horario.nome,
        carga_horaria=carga.nome,
        modalidade=modalidade.nome,
        treinamento=treinamento.nome,
        cmd=cmd.nome,
        sjb=sjb.nome,
        sag_tombos=sag.nome,
        instrutor=instrutor.nome,
        local=local.nome,
        observacao=payload.get('observacao', ''),
        sge_ativo=payload.get('sge_ativo', False),
        sge_link=payload.get('sge_link'),
    )

    try:
        db.session.add(item)
        db.session.commit()
        return jsonify({'id': item.id}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@planejamento_bp.route('/planejamento/<string:row_id>', methods=['PUT'])
def atualizar_planejamento(row_id):
    """Atualiza um item existente."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    if not _tabela_planejamento_existe():
        return (
            jsonify({'erro': 'Tabela planejamento_itens não existe; execute as migrações.'}),
            500,
        )

    item = PlanejamentoItem.query.filter_by(row_id=row_id).first()
    if not item:
        return jsonify({'erro': 'Item não encontrado'}), 404

    data = request.json or {}
    data_str = data.get('data')
    try:
        data_obj = datetime.fromisoformat(data_str).date()
    except Exception:
        return jsonify({'erro': 'Data inválida'}), 400

    item.data = data_obj
    item.semana = data.get('semana')
    item.horario = data.get('horario')
    item.carga_horaria = data.get('cargaHoraria')
    item.modalidade = data.get('modalidade')
    item.treinamento = data.get('treinamento')
    item.cmd = data.get('cmd')
    item.sjb = data.get('sjb')
    item.sag_tombos = data.get('sagTombos')
    item.instrutor = data.get('instrutor')
    item.local = data.get('local')
    item.observacao = data.get('observacao')
    item.sge_ativo = data.get('sge_ativo', item.sge_ativo)
    item.sge_link = data.get('sge_link', item.sge_link)

    try:
        db.session.commit()
        return jsonify(item.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@planejamento_bp.route('/planejamento/itens/<int:item_id>', methods=['PUT'])
def atualizar_item(item_id):
    """Atualiza um item existente de planejamento."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    if not _tabela_planejamento_existe():
        return (
            jsonify({'erro': 'Tabela planejamento_itens não existe; execute as migrações.'}),
            500,
        )

    item = PlanejamentoItem.query.get(item_id)
    if not item:
        return jsonify({'erro': 'Item não encontrado'}), 404

    data = request.json or {}
    if 'data' in data:
        try:
            item.data = datetime.fromisoformat(data['data']).date()
        except Exception:
            return jsonify({'erro': 'Data inválida'}), 400

    item.lote_id = data.get('loteId', item.lote_id)
    item.semana = data.get('semana', item.semana)
    item.horario = data.get('horario', item.horario)
    item.carga_horaria = data.get('carga_horaria', item.carga_horaria)
    item.modalidade = data.get('modalidade', item.modalidade)
    item.treinamento = data.get('treinamento', item.treinamento)
    item.cmd = data.get('cmd', item.cmd)
    item.sjb = data.get('sjb', item.sjb)
    item.sag_tombos = data.get('sag_tombos', item.sag_tombos)
    item.instrutor = data.get('instrutor', item.instrutor)
    item.local = data.get('local', item.local)
    item.observacao = data.get('observacao', item.observacao)
    item.sge_ativo = data.get('sge_ativo', item.sge_ativo)
    item.sge_link = data.get('sge_link', item.sge_link)

    try:
        db.session.commit()
        try:
            dados_do_item = item.to_dict()
            email_service.enviar_notificacao_planejamento(
                assunto="Item do Planejamento foi Atualizado",
                nome_template="email/item_planejamento_atualizado.html.j2",
                contexto={"item": dados_do_item},
            )
        except Exception as e:
            current_app.logger.error(
                f"Falha ao enviar e-mail de notificação de atualização de item {item_id}: {e}"
            )
        return jsonify(item.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@planejamento_bp.route('/planejamento/itens/<int:item_id>', methods=['DELETE'])
def excluir_item(item_id):
    """Remove um item de planejamento."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    if not _tabela_planejamento_existe():
        return (
            jsonify({'erro': 'Tabela planejamento_itens não existe; execute as migrações.'}),
            500,
        )

    item = PlanejamentoItem.query.get(item_id)
    if not item:
        return jsonify({'erro': 'Item não encontrado'}), 404

    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'mensagem': 'Item excluído com sucesso'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@planejamento_bp.route(
    '/planejamento/lote/<string:lote_id>', methods=['DELETE']
)
def excluir_lote(lote_id):
    """Remove todos os itens pertencentes a um lote."""
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    if not _tabela_planejamento_existe():
        return (
            jsonify({'erro': 'Tabela planejamento_itens não existe; execute as migrações.'}),
            500,
        )

    try:
        PlanejamentoItem.query.filter_by(lote_id=lote_id).delete(synchronize_session=False)
        db.session.commit()
        return '', 204
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@planejamento_bp.route('/planejamento/schema', methods=['GET'])
def schema_planejamento():
    """Retorna o schema esperado para o planejamento."""
    return jsonify(PlanejamentoCreateSchema.model_json_schema())
