"""Rotas para gerenciamento de ocupacoes de salas."""
from flask import Blueprint, request, jsonify, make_response, send_file, current_app
from src.models import db
from src.models.ocupacao import Ocupacao
from src.models.sala import Sala
from src.models.instrutor import Instrutor
from src.routes.user import verificar_autenticacao, verificar_admin
from src.utils.decorators import admin_required
from sqlalchemy.exc import SQLAlchemyError
from src.utils.error_handler import handle_internal_error
from datetime import datetime, date, time, timedelta
from pydantic import ValidationError
from src.schemas import OcupacaoCreateSchema, OcupacaoUpdateSchema
import csv
from io import StringIO, BytesIO
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy import and_, or_, func, extract

ocupacao_bp = Blueprint('ocupacao', __name__)

# Desabilita cache para todas as respostas deste blueprint para evitar que o
# navegador utilize dados antigos ao atualizar ou excluir ocupações.
@ocupacao_bp.after_request
def add_no_cache_headers(response):
    """Adiciona cabeçalhos para desativar cache."""
    response.headers['Cache-Control'] = 'no-store'
    return response

TURNOS_PADRAO = {
    'Manhã': (time.fromisoformat('08:00'), time.fromisoformat('12:00')),
    'Tarde': (time.fromisoformat('13:30'), time.fromisoformat('17:30')),
    'Noite': (time.fromisoformat('18:30'), time.fromisoformat('22:30'))
}

@ocupacao_bp.route('/ocupacoes', methods=['GET'])
def listar_ocupacoes():
    """
    Lista todas as ocupações com filtros opcionais.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    # Parâmetros de filtro
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    sala_id = request.args.get('sala_id', type=int)
    turno = request.args.get('turno')
    instrutor_id = request.args.get('instrutor_id', type=int)
    status = request.args.get('status')
    tipo_ocupacao = request.args.get('tipo_ocupacao')
    curso_evento = request.args.get('curso_evento')
    
    # Query base
    query = Ocupacao.query
    
    # Aplica filtros de data
    if data_inicio_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            query = query.filter(Ocupacao.data >= data_inicio)
        except ValueError:
            return jsonify({'erro': 'Formato de data_inicio inválido (YYYY-MM-DD)'}), 400
    
    if data_fim_str:
        try:
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
            query = query.filter(Ocupacao.data <= data_fim)
        except ValueError:
            return jsonify({'erro': 'Formato de data_fim inválido (YYYY-MM-DD)'}), 400
    
    # Aplica outros filtros
    if sala_id:
        query = query.filter(Ocupacao.sala_id == sala_id)
    
    if instrutor_id:
        query = query.filter(Ocupacao.instrutor_id == instrutor_id)
    
    if status:
        query = query.filter(Ocupacao.status == status)
    
    if tipo_ocupacao:
        query = query.filter(Ocupacao.tipo_ocupacao == tipo_ocupacao)
    
    if curso_evento:
        query = query.filter(Ocupacao.curso_evento.ilike(f'%{curso_evento}%'))
    
    # Controle de acesso: usuários comuns só veem suas próprias ocupações
    if not verificar_admin(user):
        query = query.filter(Ocupacao.usuario_id == user.id)
    
    # Ordena por data e horário
    ocupacoes = query.order_by(Ocupacao.data, Ocupacao.horario_inicio).all()

    return jsonify([ocupacao.to_dict() for ocupacao in ocupacoes])


@ocupacao_bp.route('/ocupacoes/export', methods=['GET'])
def exportar_ocupacoes():
    """Exporta ocupações em CSV, PDF ou XLSX."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    formato = request.args.get('formato', 'csv').lower()

    if verificar_admin(user):
        ocupacoes = Ocupacao.query.all()
    else:
        ocupacoes = Ocupacao.query.filter_by(usuario_id=user.id).all()

    if formato == 'pdf':
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(50, 750, "Relatório de Ocupações")
        y = 730
        c.drawString(50, y, "ID  Sala  Data  Início  Fim  Status")
        y -= 20
        for oc in ocupacoes:
            sala = oc.sala.nome if oc.sala else oc.sala_id
            c.drawString(50, y, f"{oc.id}  {sala}  {oc.data}  {oc.horario_inicio}  {oc.horario_fim}  {oc.status}")
            y -= 20
            if y < 50:
                c.showPage()
                y = 750
        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name='ocupacoes.pdf')

    if formato == 'xlsx':
        wb = Workbook()
        ws = wb.active
        ws.append(["ID", "Sala", "Data", "Início", "Fim", "Status"])
        for oc in ocupacoes:
            sala = oc.sala.nome if oc.sala else oc.sala_id
            ws.append([oc.id, sala, oc.data, oc.horario_inicio, oc.horario_fim, oc.status])
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='ocupacoes.xlsx'
        )

    # CSV padrão
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID", "Sala", "Data", "Início", "Fim", "Status"])
    for oc in ocupacoes:
        sala = oc.sala.nome if oc.sala else oc.sala_id
        writer.writerow([oc.id, sala, oc.data, oc.horario_inicio, oc.horario_fim, oc.status])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=ocupacoes.csv"
    output.headers["Content-Type"] = "text/csv"
    return output

@ocupacao_bp.route('/ocupacoes/<int:id>', methods=['GET'])
def obter_ocupacao(id):
    """Obtém detalhes de uma ocupação específica incluindo o período completo."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    ocupacao = db.session.get(Ocupacao, id)
    if not ocupacao:
        return jsonify({'erro': 'Ocupação não encontrada'}), 404

    # Controle de acesso: usuários comuns só podem ver suas próprias ocupações
    if not verificar_admin(user) and ocupacao.usuario_id != user.id:
        return jsonify({'erro': 'Permissão negada'}), 403

    dados = ocupacao.to_dict()

    # Calcula o período completo da reserva
    data_inicio = ocupacao.data
    data_fim = ocupacao.data
    if ocupacao.grupo_ocupacao_id:
        grupo_ocupacoes = Ocupacao.query.filter_by(grupo_ocupacao_id=ocupacao.grupo_ocupacao_id).all()
        if grupo_ocupacoes:
            datas = [oc.data for oc in grupo_ocupacoes]
            data_inicio = min(datas)
            data_fim = max(datas)

    dados['data_inicio'] = data_inicio.isoformat()
    dados['data_fim'] = data_fim.isoformat()

    return jsonify(dados)

@ocupacao_bp.route('/ocupacoes', methods=['POST'])
@admin_required()
def criar_ocupacao():
    """
    Cria uma nova ocupação.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    data = request.json or {}
    try:
        payload = OcupacaoCreateSchema(**data)
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400

    sala = db.session.get(Sala, payload.sala_id)
    if not sala:
        return jsonify({'erro': 'Sala não encontrada'}), 404

    # Verifica se o instrutor existe (se fornecido)
    instrutor = None
    if payload.instrutor_id:
        instrutor = db.session.get(Instrutor, payload.instrutor_id)
        if not instrutor:
            return jsonify({'erro': 'Instrutor não encontrado'}), 404
    
    try:
        data_inicio = (
            datetime.strptime(payload.data_inicio, '%Y-%m-%d').date()
            if payload.data_inicio else ocupacao_original.data
        )
        data_fim = (
            datetime.strptime(payload.data_fim, '%Y-%m-%d').date()
            if payload.data_fim else ocupacao_original.data
        )

        if data_inicio > data_fim:
            return jsonify({'erro': 'Data de início deve ser anterior ou igual à data de fim'}), 400


        if payload.turno not in TURNOS_PADRAO:
            return jsonify({'erro': 'Turno inválido'}), 400

        horario_inicio, horario_fim = TURNOS_PADRAO[payload.turno]

        conflitos_totais = []
        dia = data_inicio
        while dia <= data_fim:
            if not sala.is_disponivel(dia, horario_inicio, horario_fim):
                conflitos = Ocupacao.buscar_conflitos(payload.sala_id, dia, horario_inicio, horario_fim)
                conflitos_totais.extend(conflitos)
            dia += timedelta(days=1)

        if conflitos_totais:
            return jsonify({
                'erro': 'Sala não disponível no turno solicitado',
                'conflitos': [c.to_dict(include_relations=False) for c in conflitos_totais]
            }), 409
        
        # Verifica disponibilidade do instrutor (se fornecido)
        if instrutor:
            ocupacoes_instrutor = []
            dia = data_inicio
            while dia <= data_fim:
                ocorrencias = Ocupacao.query.filter(
                    Ocupacao.instrutor_id == instrutor.id,
                    Ocupacao.data == dia,
                    Ocupacao.status.in_(['confirmado', 'pendente']),
                    or_(
                        and_(Ocupacao.horario_inicio <= horario_inicio, Ocupacao.horario_fim > horario_inicio),
                        and_(Ocupacao.horario_inicio < horario_fim, Ocupacao.horario_fim >= horario_fim),
                        and_(Ocupacao.horario_inicio >= horario_inicio, Ocupacao.horario_fim <= horario_fim)
                    )
                ).all()
                ocupacoes_instrutor.extend(ocorrencias)
                dia += timedelta(days=1)

            if ocupacoes_instrutor:
                return jsonify({
                    'erro': 'Instrutor não disponível no turno solicitado',
                    'conflitos': [c.to_dict(include_relations=False) for c in ocupacoes_instrutor]
                }), 409
        
        # Validação de tipo de ocupação
        tipos_validos = ['aula_regular', 'evento_especial', 'reuniao', 'manutencao', 'reserva_especial']
        tipo_ocupacao = payload.tipo_ocupacao or 'aula_regular'
        if tipo_ocupacao not in tipos_validos:
            return jsonify({'erro': f'Tipo de ocupação deve ser um dos seguintes: {", ".join(tipos_validos)}'}), 400

        # Validação de recorrência
        recorrencias_validas = ['unica', 'semanal', 'mensal']
        recorrencia = payload.recorrencia or 'unica'
        if recorrencia not in recorrencias_validas:
            return jsonify({'erro': f'Recorrência deve ser uma das seguintes: {", ".join(recorrencias_validas)}'}), 400
        
        import uuid
        grupo_id = uuid.uuid4().hex

        ocupacoes_criadas = []
        dia = data_inicio
        while dia <= data_fim:
            # Se o tipo de ocupação for 'aula_regular' e o dia for sábado ou domingo, ignora
            if payload.tipo_ocupacao == 'aula_regular' and dia.weekday() >= 5:
                dia += timedelta(days=1)
                continue
            nova_ocupacao = Ocupacao(
                sala_id=payload.sala_id,
                instrutor_id=payload.instrutor_id,
                usuario_id=user.id,
                curso_evento=payload.curso_evento,
                data=dia,
                horario_inicio=horario_inicio,
                horario_fim=horario_fim,
                tipo_ocupacao=tipo_ocupacao,
                recorrencia=recorrencia,
                status=payload.status or 'confirmado',
                observacoes=payload.observacoes,
                grupo_ocupacao_id=grupo_id
            )
            db.session.add(nova_ocupacao)
            ocupacoes_criadas.append(nova_ocupacao)
            dia += timedelta(days=1)

        db.session.commit()

        return jsonify([o.to_dict() for o in ocupacoes_criadas]), 201
        
    except ValueError:
        return jsonify({'erro': 'Formato de data ou horário inválido'}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@ocupacao_bp.route('/ocupacoes/<int:id>', methods=['PUT'])
@admin_required()
def atualizar_ocupacao(id):
    """
    Atualiza uma ocupação existente. Para garantir a consistência de agendamentos
    de múltiplos dias, esta função adota a estratégia de "apagar e recriar".
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    # 1. Encontra a ocupação original para obter o grupo.
    ocupacao_original = db.session.get(Ocupacao, id)
    if not ocupacao_original:
        return jsonify({'erro': 'Ocupação não encontrada'}), 404

    # 2. Verifica as permissões do usuário.
    if not ocupacao_original.pode_ser_editada_por(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    # 3. Valida os novos dados recebidos do formulário.
    data = request.json or {}
    try:
        payload = OcupacaoUpdateSchema(**data)
    except ValidationError as e:
        return jsonify({'erro': e.errors()}), 400

    # 4. Pega o grupo_id original. Se não existir, usa um novo.
    grupo_id = ocupacao_original.grupo_ocupacao_id
    if not grupo_id:
        import uuid
        grupo_id = uuid.uuid4().hex

    # ----- Início da Transação Atómica -----
    try:
        # 5. Apaga TODAS as ocupações antigas que pertencem ao mesmo grupo.
        Ocupacao.query.filter_by(grupo_ocupacao_id=grupo_id).delete()

        # 6. Prepara os dados para a recriação.
        sala_id = payload.sala_id if payload.sala_id is not None else ocupacao_original.sala_id
        instrutor_id = payload.instrutor_id if payload.instrutor_id is not None else ocupacao_original.instrutor_id
        data_inicio = payload.data_inicio and datetime.strptime(payload.data_inicio, "%Y-%m-%d").date() or ocupacao_original.data
        data_fim = payload.data_fim and datetime.strptime(payload.data_fim, "%Y-%m-%d").date() or ocupacao_original.data
        turno = payload.turno if payload.turno is not None else ocupacao_original.get_turno()

        if data_inicio > data_fim:
            raise ValueError("Data de início não pode ser posterior à data de fim.")

        if turno not in TURNOS_PADRAO:
            raise ValueError("Turno inválido.")
        horario_inicio, horario_fim = TURNOS_PADRAO[turno]

        # 7. Verifica conflitos com outras ocupações, ignorando o grupo atual (que já foi apagado).
        conflitos = Ocupacao.query.filter(
            Ocupacao.sala_id == sala_id,
            Ocupacao.data.between(data_inicio, data_fim),
            Ocupacao.horario_inicio == horario_inicio,
            # Adicionar verificação de conflito de instrutor se necessário
        ).all()

        if conflitos:
             raise ValueError("Conflito de horário detectado. A sala já está ocupada neste novo período.")

        # 8. Recria as novas ocupações com os dados atualizados.
        ocupacoes_criadas = []
        dia_atual = data_inicio
        while dia_atual <= data_fim:
            # Se o tipo de ocupação for 'aula_regular' e o dia for sábado ou domingo, ignora
            if payload.tipo_ocupacao == 'aula_regular' and dia_atual.weekday() >= 5:
                dia_atual += timedelta(days=1)
                continue
            nova_ocupacao = Ocupacao(
                sala_id=sala_id,
                instrutor_id=instrutor_id,
                usuario_id=user.id,
                curso_evento=payload.curso_evento,
                data=dia_atual,
                horario_inicio=horario_inicio,
                horario_fim=horario_fim,
                tipo_ocupacao=payload.tipo_ocupacao,
                recorrencia=payload.recorrencia,
                status=payload.status,
                observacoes=payload.observacoes,
                grupo_ocupacao_id=grupo_id  # Reutiliza o mesmo ID de grupo
            )
            db.session.add(nova_ocupacao)
            ocupacoes_criadas.append(nova_ocupacao)
            dia_atual += timedelta(days=1)
        
        # 9. Comita a transação.
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Ocupação atualizada com sucesso!',
            'ocupacoes': [o.to_dict() for o in ocupacoes_criadas]
        }), 200

    except ValueError as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        # 10. Se qualquer passo falhar, desfaz tudo (rollback).
        db.session.rollback()
        return jsonify({'erro': f'Falha ao atualizar a ocupação: {str(e)}'}), 500
@ocupacao_bp.route('/ocupacoes/<int:id>', methods=['DELETE'])
@admin_required()
def remover_ocupacao(id):
    """
    Remove uma ocupação.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    ocupacao = db.session.get(Ocupacao, id)
    if not ocupacao:
        return jsonify({'erro': 'Ocupação não encontrada'}), 404
    
    # Verifica permissões
    if not ocupacao.pode_ser_editada_por(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    
    try:
        somente_dia = request.args.get('somente_dia', default=False, type=lambda v: str(v).lower() == 'true')
        grupo_id = ocupacao.grupo_ocupacao_id

        if somente_dia or not grupo_id:
            ocupacoes = [ocupacao]
        else:
            ocupacoes = Ocupacao.query.filter_by(grupo_ocupacao_id=grupo_id).all()

        quantidade = len(ocupacoes)
        for oc in ocupacoes:
            db.session.delete(oc)

        db.session.commit()
        return jsonify({'mensagem': 'Ocupação removida com sucesso', 'removidas': quantidade})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@ocupacao_bp.route('/ocupacoes/verificar-disponibilidade', methods=['GET'])
def verificar_disponibilidade():
    """
    Verifica a disponibilidade de uma sala em uma data e horário específicos.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    # Parâmetros obrigatórios
    sala_id = request.args.get('sala_id', type=int)
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    turno = request.args.get('turno')
    ocupacao_id = request.args.get('ocupacao_id', type=int)  # Para edição
    grupo_ocupacao_id = None
    if ocupacao_id:
        ocup = db.session.get(Ocupacao, ocupacao_id)
        if ocup:
            grupo_ocupacao_id = ocup.grupo_ocupacao_id

    if not all([sala_id, data_inicio_str, data_fim_str, turno]):
        return jsonify({'erro': 'Parâmetros obrigatórios: sala_id, data_inicio, data_fim, turno'}), 400
    
    # Verifica se a sala existe
    sala = db.session.get(Sala, sala_id)
    if not sala:
        return jsonify({'erro': 'Sala não encontrada'}), 404
    
    try:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()

        if data_inicio > data_fim:
            return jsonify({'erro': 'Data de início deve ser anterior ou igual à data de fim'}), 400

        if turno not in TURNOS_PADRAO:
            return jsonify({'erro': 'Turno inválido'}), 400

        horario_inicio, horario_fim = TURNOS_PADRAO[turno]

        disponivel = True
        conflitos = []
        dia = data_inicio
        while dia <= data_fim:
            if not sala.is_disponivel(dia, horario_inicio, horario_fim, ocupacao_id, grupo_ocupacao_id):
                disponivel = False
                conflitos.extend(Ocupacao.buscar_conflitos(sala_id, dia, horario_inicio, horario_fim, ocupacao_id, grupo_ocupacao_id))
            dia += timedelta(days=1)
        
        return jsonify({
            'disponivel': disponivel,
            'sala': sala.to_dict(),
            'conflitos': conflitos
        })
        
    except ValueError:
        return jsonify({'erro': 'Formato de data ou horário inválido'}), 400
    except SQLAlchemyError as e:
        return handle_internal_error(e)

@ocupacao_bp.route('/ocupacoes/calendario', methods=['GET'])
def obter_ocupacoes_calendario():
    """
    Obtém ocupações formatadas para exibição em calendário.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    # Parâmetros de filtro
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    sala_id = request.args.get('sala_id', type=int)
    instrutor_id = request.args.get('instrutor_id', type=int)
    turno = request.args.get('turno')

    # Define período padrão (mês atual) se não fornecido
    if not data_inicio_str or not data_fim_str:
        hoje = date.today()
        primeiro_dia = hoje.replace(day=1)
        if hoje.month == 12:
            ultimo_dia = date(hoje.year + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)
        
        data_inicio = primeiro_dia
        data_fim = ultimo_dia
    else:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido (YYYY-MM-DD)'}), 400
    
    # Query base
    query = Ocupacao.query.filter(
        Ocupacao.data >= data_inicio,
        Ocupacao.data <= data_fim,
        Ocupacao.status.in_(['confirmado', 'pendente'])
    )
    
    # Aplica filtro de sala se fornecido
    if sala_id:
        query = query.filter(Ocupacao.sala_id == sala_id)

    # Aplica filtro de instrutor se fornecido
    if instrutor_id:
        query = query.filter(Ocupacao.instrutor_id == instrutor_id)

    # Aplica filtro de turno se fornecido
    if turno:
        if turno not in TURNOS_PADRAO:
            return jsonify({'erro': 'Turno inválido'}), 400
        inicio, fim = TURNOS_PADRAO[turno]
        query = query.filter(
            Ocupacao.horario_inicio == inicio,
            Ocupacao.horario_fim == fim
        )
    
    # Controle de acesso: usuários comuns só veem suas próprias ocupações
    if not verificar_admin(user):
        query = query.filter(Ocupacao.usuario_id == user.id)
    
    ocupacoes = query.order_by(Ocupacao.data, Ocupacao.horario_inicio).all()
    
    # Formata para o calendário
    def cor_turno(t):
        """Retorna a cor associada ao turno."""
        cores = {
            'Manhã': '#FFEB3B',
            'Tarde': '#03A9F4',
            'Noite': '#673AB7'
        }
        return cores.get(t, '#607D8B')

    eventos_calendario = []
    for ocupacao in ocupacoes:
        turno_evento = ocupacao.get_turno()
        cor = cor_turno(turno_evento)
        evento = {
            'id': ocupacao.id,
            # Exibe apenas o turno no calendário mensal para evitar poluição visual
            'title': turno_evento,
            'start': f"{ocupacao.data}T{ocupacao.horario_inicio}",
            'end': f"{ocupacao.data}T{ocupacao.horario_fim}",
            'backgroundColor': cor,
            'borderColor': cor,
            'extendedProps': ocupacao.to_dict()
        }
        eventos_calendario.append(evento)

    return jsonify(eventos_calendario)


@ocupacao_bp.route('/ocupacoes/resumo-periodo', methods=['GET'])
def obter_resumo_periodo():
    """Retorna resumo de salas ocupadas e livres por dia e turno."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    sala_id = request.args.get('sala_id', type=int)
    instrutor_id = request.args.get('instrutor_id', type=int)
    turno_filtro = request.args.get('turno')

    if not data_inicio_str or not data_fim_str:
        hoje = date.today()
        primeiro_dia = hoje.replace(day=1)
        if hoje.month == 12:
            ultimo_dia = date(hoje.year + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)

        data_inicio = primeiro_dia
        data_fim = ultimo_dia
    else:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido (YYYY-MM-DD)'}), 400

    salas_ativas = Sala.query.filter_by(status='ativa').all()
    total_salas = len(salas_ativas)
    salas_dict = {s.id: s.nome for s in salas_ativas}

    query = Ocupacao.query.filter(
        Ocupacao.data >= data_inicio,
        Ocupacao.data <= data_fim,
        Ocupacao.status.in_(['confirmado', 'pendente'])
    )

    if sala_id:
        query = query.filter(Ocupacao.sala_id == sala_id)

    if instrutor_id:
        query = query.filter(Ocupacao.instrutor_id == instrutor_id)

    if turno_filtro:
        if turno_filtro not in TURNOS_PADRAO:
            return jsonify({'erro': 'Turno inválido'}), 400
        inicio, fim = TURNOS_PADRAO[turno_filtro]
        query = query.filter(
            Ocupacao.horario_inicio == inicio,
            Ocupacao.horario_fim == fim
        )

    if not verificar_admin(user):
        query = query.filter(Ocupacao.usuario_id == user.id)

    ocupacoes = query.all()

    resumo = {}
    dia = data_inicio
    while dia <= data_fim:
        resumo[dia.isoformat()] = {
            turno: {
                'ocupadas': 0,
                'salas_ocupadas': [],
                'salas_livres': [],
                'total_salas': total_salas
            } for turno in TURNOS_PADRAO
        }
        dia += timedelta(days=1)

    for oc in ocupacoes:
        turno = oc.get_turno()
        if not turno:
            continue
        info = resumo[oc.data.isoformat()][turno]
        info['ocupadas'] += 1
        info['salas_ocupadas'].append({
            'sala_id': oc.sala_id,
            'sala_nome': salas_dict.get(oc.sala_id, str(oc.sala_id)),
            'curso_evento': oc.curso_evento,
            'instrutor_nome': oc.instrutor.nome if oc.instrutor else None
        })

    for dia_key, turnos in resumo.items():
        for turno, info in turnos.items():
            ocupadas_ids = [s['sala_id'] for s in info['salas_ocupadas']]
            info['salas_livres'] = [nome for sid, nome in salas_dict.items() if sid not in ocupadas_ids]
            info['livres'] = info['total_salas'] - info['ocupadas']

    return jsonify(resumo)

@ocupacao_bp.route('/ocupacoes/tipos', methods=['GET'])
def listar_tipos_ocupacao():
    """
    Lista os tipos de ocupação disponíveis.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    tipos = [
        {'valor': 'aula_regular', 'nome': 'Aula Regular', 'cor': '#4CAF50'},
        {'valor': 'evento_especial', 'nome': 'Evento Especial', 'cor': '#FF9800'},
        {'valor': 'reuniao', 'nome': 'Reunião', 'cor': '#2196F3'},
        {'valor': 'manutencao', 'nome': 'Manutenção', 'cor': '#F44336'},
        {'valor': 'reserva_especial', 'nome': 'Reserva Especial', 'cor': '#9C27B0'}
    ]
    
    return jsonify(tipos)

@ocupacao_bp.route('/ocupacoes/relatorio', methods=['GET'])
def gerar_relatorio_ocupacoes():
    """
    Gera relatório de ocupações com estatísticas.
    Apenas administradores podem acessar.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403
    
    # Parâmetros de filtro
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    
    # Define período padrão (mês atual) se não fornecido
    if not data_inicio_str or not data_fim_str:
        hoje = date.today()
        primeiro_dia = hoje.replace(day=1)
        if hoje.month == 12:
            ultimo_dia = date(hoje.year + 1, 1, 1) - timedelta(days=1)
        else:
            ultimo_dia = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)
        
        data_inicio = primeiro_dia
        data_fim = ultimo_dia
    else:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido (YYYY-MM-DD)'}), 400
    
    # Estatísticas gerais
    total_ocupacoes = Ocupacao.query.filter(
        Ocupacao.data >= data_inicio,
        Ocupacao.data <= data_fim
    ).count()
    
    ocupacoes_confirmadas = Ocupacao.query.filter(
        Ocupacao.data >= data_inicio,
        Ocupacao.data <= data_fim,
        Ocupacao.status == 'confirmado'
    ).count()
    
    ocupacoes_pendentes = Ocupacao.query.filter(
        Ocupacao.data >= data_inicio,
        Ocupacao.data <= data_fim,
        Ocupacao.status == 'pendente'
    ).count()
    
    ocupacoes_canceladas = Ocupacao.query.filter(
        Ocupacao.data >= data_inicio,
        Ocupacao.data <= data_fim,
        Ocupacao.status == 'cancelado'
    ).count()
    
    # Estatísticas por sala
    salas_mais_utilizadas = db.session.query(
        Sala.nome,
        db.func.count(Ocupacao.id).label('total_ocupacoes')
    ).join(Ocupacao).filter(
        Ocupacao.data >= data_inicio,
        Ocupacao.data <= data_fim,
        Ocupacao.status.in_(['confirmado', 'pendente'])
    ).group_by(Sala.id, Sala.nome).order_by(db.desc('total_ocupacoes')).limit(10).all()
    
    # Estatísticas por tipo de ocupação
    ocupacoes_por_tipo = db.session.query(
        Ocupacao.tipo_ocupacao,
        db.func.count(Ocupacao.id).label('total')
    ).filter(
        Ocupacao.data >= data_inicio,
        Ocupacao.data <= data_fim,
        Ocupacao.status.in_(['confirmado', 'pendente'])
    ).group_by(Ocupacao.tipo_ocupacao).all()
    
    relatorio = {
        'periodo': {
            'data_inicio': data_inicio.isoformat(),
            'data_fim': data_fim.isoformat()
        },
        'estatisticas_gerais': {
            'total_ocupacoes': total_ocupacoes,
            'ocupacoes_confirmadas': ocupacoes_confirmadas,
            'ocupacoes_pendentes': ocupacoes_pendentes,
            'ocupacoes_canceladas': ocupacoes_canceladas
        },
        'salas_mais_utilizadas': [
            {'sala': sala, 'total_ocupacoes': total} 
            for sala, total in salas_mais_utilizadas
        ],
        'ocupacoes_por_tipo': [
            {'tipo': tipo or 'Não especificado', 'total': total} 
            for tipo, total in ocupacoes_por_tipo
        ]
    }

    return jsonify(relatorio)


@ocupacao_bp.route('/ocupacoes/tendencia', methods=['GET'])
def obter_tendencia_ocupacoes():
    """Retorna total de ocupações por mês do ano informado."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    if not verificar_admin(user):
        return jsonify({'erro': 'Permissão negada'}), 403

    ano = request.args.get('ano', type=int, default=date.today().year)

    resultados = db.session.query(
        extract('month', Ocupacao.data).label('mes'),
        func.count(Ocupacao.id).label('total')
    ).filter(
        extract('year', Ocupacao.data) == ano
    ).group_by(extract('month', Ocupacao.data)).order_by(extract('month', Ocupacao.data)).all()

    dados_meses = {str(r.mes).zfill(2): r.total for r in resultados}
    dados_formatados = []
    for i in range(1, 13):
        mes_str = str(i).zfill(2)
        dados_formatados.append({
            'mes': mes_str,
            'total': dados_meses.get(mes_str, 0)
        })

    return jsonify(dados_formatados)

