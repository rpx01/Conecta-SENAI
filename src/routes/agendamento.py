"""Rotas de agendamento de laboratorios."""
from flask import Blueprint, request, jsonify, make_response, send_file, g
from datetime import datetime, date, timedelta
import json
import calendar
import csv
from io import StringIO, BytesIO
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from src.models import db
from src.models.agendamento import Agendamento
from src.models.laboratorio_turma import Laboratorio, Turma
from src.models.user import User
from src.routes.user import verificar_autenticacao, verificar_admin
from src.auth import login_required
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, extract
from src.utils.error_handler import handle_internal_error
from src.utils.audit import log_action

agendamento_bp = Blueprint('agendamento', __name__)

@agendamento_bp.route('/agendamentos', methods=['GET'])
def listar_agendamentos():
    """
    Lista todos os agendamentos.
    Usuários comuns veem apenas seus próprios agendamentos.
    Administradores veem todos os agendamentos.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    if verificar_admin(user):
        # Administradores veem todos os agendamentos
        agendamentos = Agendamento.query.all()
    else:
        # Usuários comuns veem apenas seus próprios agendamentos
        agendamentos = Agendamento.query.filter_by(usuario_id=user.id).all()
    
    return jsonify([a.to_dict() for a in agendamentos])

@agendamento_bp.route('/agendamentos/<int:id>', methods=['GET'])
def obter_agendamento(id):
    """
    Obtém detalhes de um agendamento específico.
    Usuários comuns só podem ver seus próprios agendamentos.
    Administradores podem ver qualquer agendamento.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        return jsonify({'erro': 'Agendamento não encontrado'}), 404
    
    # Verifica permissões
    if not verificar_admin(user) and agendamento.usuario_id != user.id:
        return jsonify({'erro': 'Permissão negada'}), 403

    return jsonify(agendamento.to_dict())

@agendamento_bp.route('/agendamentos/<int:id>/detalhes', methods=['GET'])
def obter_agendamento_detalhes(id):
    """Retorna detalhes completos de um agendamento, incluindo nome do usuário."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        return jsonify({'erro': 'Agendamento não encontrado'}), 404

    dados = agendamento.to_dict()
    dados['usuario_nome'] = agendamento.usuario.nome if agendamento.usuario else None
    return jsonify(dados)

@agendamento_bp.route('/agendamentos', methods=['POST'])
@login_required
def criar_agendamento():
    """
    Cria um novo agendamento.
    Usuários comuns só podem criar agendamentos para si mesmos.
    Administradores podem criar agendamentos para qualquer usuário.
    """
    user = g.current_user
    
    data = request.json
    
    # Validação de dados
    campos_obrigatorios = ['data', 'laboratorio', 'turma', 'turno', 'horarios']
    if not all(campo in data for campo in campos_obrigatorios):
        return jsonify({'erro': 'Dados incompletos'}), 400
    
    # Verifica o formato da data
    try:
        data_agendamento = datetime.strptime(data['data'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'erro': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
    
    # Verifica o formato dos horários (deve ser uma string JSON válida)
    try:
        horarios = json.loads(data['horarios']) if isinstance(data['horarios'], str) else data['horarios']
    except json.JSONDecodeError:
        return jsonify({'erro': 'Formato de horários inválido'}), 400
    
    # Determina o usuário para o qual o agendamento será criado
    usuario_id = data.get('usuario_id', user.id)
    
    # Usuários comuns só podem criar agendamentos para si mesmos
    if not verificar_admin(user) and usuario_id != user.id:
        return jsonify({'erro': 'Permissão negada'}), 403
    
    # Verifica se o usuário existe
    if usuario_id != user.id:
        usuario_destino = db.session.get(User, usuario_id)
        if not usuario_destino:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
    
    # Verifica conflitos de horários
    conflitos = verificar_conflitos_horarios(
        data_agendamento,
        data['laboratorio'],
        horarios,
        None
    )
    
    if conflitos:
        return jsonify({'erro': 'Conflito de horários', 'conflitos': conflitos}), 409
    
    # Cria o agendamento
    try:
        novo_agendamento = Agendamento(
            data=data_agendamento,
            laboratorio=data['laboratorio'],
            turma=data['turma'],
            turno=data['turno'],
            horarios=horarios,
            usuario_id=usuario_id
        )
        db.session.add(novo_agendamento)
        db.session.commit()
        log_action(user.id, 'create', 'Agendamento', novo_agendamento.id, novo_agendamento.to_dict())
        return jsonify(novo_agendamento.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@agendamento_bp.route('/agendamentos/<int:id>', methods=['PUT'])
def atualizar_agendamento(id):
    """
    Atualiza um agendamento existente.
    Usuários comuns só podem atualizar seus próprios agendamentos.
    Administradores podem atualizar qualquer agendamento.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        return jsonify({'erro': 'Agendamento não encontrado'}), 404
    
    # Verifica permissões
    if not verificar_admin(user) and agendamento.usuario_id != user.id:
        return jsonify({'erro': 'Permissão negada'}), 403
    
    data = request.json
    
    # Processa a data se fornecida
    data_agendamento = agendamento.data
    if 'data' in data:
        try:
            data_agendamento = datetime.strptime(data['data'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
    
    # Processa os horários se fornecidos
    horarios_lista = agendamento.horarios
    if 'horarios' in data:
        try:
            horarios = json.loads(data['horarios']) if isinstance(data['horarios'], str) else data['horarios']
            horarios_lista = horarios
        except json.JSONDecodeError:
            return jsonify({'erro': 'Formato de horários inválido'}), 400
    
    # Verifica conflitos de horários
    laboratorio = data.get('laboratorio', agendamento.laboratorio)
    conflitos = verificar_conflitos_horarios(
        data_agendamento,
        laboratorio,
        horarios_lista,
        id  # ID do agendamento atual para excluir da verificação
    )
    
    if conflitos:
        return jsonify({'erro': 'Conflito de horários', 'conflitos': conflitos}), 409
    
    # Atualiza os campos fornecidos
    if 'data' in data:
        agendamento.data = data_agendamento
    if 'laboratorio' in data:
        agendamento.laboratorio = data['laboratorio']
    if 'turma' in data:
        agendamento.turma = data['turma']
    if 'turno' in data:
        agendamento.turno = data['turno']
    if 'horarios' in data:
        agendamento.horarios = horarios_lista
    
    # Apenas administradores podem alterar o usuário responsável
    if 'usuario_id' in data and verificar_admin(user):
        usuario_destino = db.session.get(User, data['usuario_id'])
        if not usuario_destino:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
        agendamento.usuario_id = data['usuario_id']
    
    try:
        db.session.commit()
        log_action(user.id, 'update', 'Agendamento', agendamento.id, agendamento.to_dict())
        return jsonify(agendamento.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)

@agendamento_bp.route('/agendamentos/<int:id>', methods=['DELETE'])
def remover_agendamento(id):
    """
    Remove um agendamento.
    Usuários comuns só podem remover seus próprios agendamentos.
    Administradores podem remover qualquer agendamento.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    agendamento = db.session.get(Agendamento, id)
    if not agendamento:
        return jsonify({'erro': 'Agendamento não encontrado'}), 404
    
    # Verifica permissões
    if not verificar_admin(user) and agendamento.usuario_id != user.id:
        return jsonify({'erro': 'Permissão negada'}), 403
    
    try:
        db.session.delete(agendamento)
        db.session.commit()
        log_action(user.id, 'delete', 'Agendamento', agendamento.id, agendamento.to_dict())
        return jsonify({'mensagem': 'Agendamento removido com sucesso'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@agendamento_bp.route('/agendamentos/calendario/<int:mes>/<int:ano>', methods=['GET'])
def agendamentos_calendario(mes, ano):
    """
    Obtém agendamentos para visualização em calendário.
    Filtra por mês e ano especificados.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401
    
    # Valida o mês e ano
    if not (1 <= mes <= 12):
        return jsonify({'erro': 'Mês inválido'}), 400
    
    if ano < 2000 or ano > 2100:  # Validação simples de ano
        return jsonify({'erro': 'Ano inválido'}), 400
    
    # Cria datas de início e fim do mês
    inicio_mes = datetime(ano, mes, 1).date()
    if mes == 12:
        fim_mes = datetime(ano + 1, 1, 1).date()
    else:
        fim_mes = datetime(ano, mes + 1, 1).date()
    
    # Consulta agendamentos no período
    if verificar_admin(user):
        # Administradores veem todos os agendamentos
        agendamentos = Agendamento.query.filter(
            Agendamento.data >= inicio_mes,
            Agendamento.data < fim_mes
        ).all()
    else:
        # Usuários comuns veem apenas seus próprios agendamentos
        agendamentos = Agendamento.query.filter(
            Agendamento.data >= inicio_mes,
            Agendamento.data < fim_mes,
            Agendamento.usuario_id == user.id
        ).all()
    
    return jsonify([a.to_dict() for a in agendamentos])


@agendamento_bp.route('/agendamentos/calendario', methods=['GET'])
def agendamentos_calendario_periodo():
    """Retorna agendamentos formatados para o componente de calendário.
    Aceita parâmetros de data_inicio e data_fim (YYYY-MM-DD) e filtros opcionais
    de laboratório e turno."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    if not data_inicio_str or not data_fim_str:
        return jsonify({'erro': 'Parâmetros de data inválidos'}), 400
    try:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'erro': 'Formato de data inválido'}), 400

    query = Agendamento.query.filter(
        Agendamento.data >= data_inicio,
        Agendamento.data <= data_fim
    )

    laboratorio = request.args.get('laboratorio')
    turno = request.args.get('turno')
    if laboratorio:
        query = query.filter(Agendamento.laboratorio == laboratorio)
    if turno:
        query = query.filter(Agendamento.turno == turno)

    if not verificar_admin(user):
        query = query.filter(Agendamento.usuario_id == user.id)

    agendamentos = query.order_by(Agendamento.data).all()

    def cor_turno(t):
        """Retorna a cor correspondente ao turno."""
        cores = {
            'Manhã': '#F3B54E',
            'Tarde': '#FFC107',
            'Noite': '#164194'
        }
        return cores.get(t, '#607D8B')

    eventos = []
    for a in agendamentos:
        eventos.append({
            'id': a.id,
            'title': f"{a.laboratorio} - {a.turma}",
            'start': a.data.isoformat(),
            'end': a.data.isoformat(),
            'backgroundColor': cor_turno(a.turno),
            'borderColor': cor_turno(a.turno),
            'extendedProps': a.to_dict()
        })
    return jsonify(eventos)


@agendamento_bp.route('/agendamentos/resumo-calendario', methods=['GET'])
def agendamentos_resumo_calendario():
    """
    Retorna um resumo de agendamentos para o novo calendário, espelhando a lógica do resumo de ocupações.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    try:
        data_inicio = datetime.strptime(request.args.get('data_inicio'), '%Y-%m-%d').date()
        data_fim = datetime.strptime(request.args.get('data_fim'), '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'erro': 'Parâmetros de data inválidos ou ausentes'}), 400

    # Filtros
    laboratorio_filtro = request.args.get('laboratorio')
    turno_filtro = request.args.get('turno')

    # Query base para os laboratórios
    labs_query = Laboratorio.query
    if laboratorio_filtro:
        labs_query = labs_query.filter(Laboratorio.nome == laboratorio_filtro)

    total_laboratorios = labs_query.count()

    # Query base para os agendamentos
    agendamentos_query = db.session.query(
        Agendamento.data,
        Agendamento.turno,
        db.func.count(Agendamento.id).label('ocupados')
    ).filter(
        Agendamento.data.between(data_inicio, data_fim)
    )

    # Aplica filtros à query de agendamentos
    if laboratorio_filtro:
        agendamentos_query = agendamentos_query.filter(Agendamento.laboratorio == laboratorio_filtro)
    if turno_filtro:
        agendamentos_query = agendamentos_query.filter(Agendamento.turno == turno_filtro)

    q = agendamentos_query.group_by(Agendamento.data, Agendamento.turno).all()

    # Monta o objeto de resumo
    resumo = {}
    for data, turno, ocupados in q:
        data_iso = data.isoformat()
        if data_iso not in resumo:
            resumo[data_iso] = {}
        resumo[data_iso][turno] = {'ocupados': ocupados}

    return jsonify({
        "total_recursos": total_laboratorios,
        "resumo": resumo
    })


@agendamento_bp.route('/agendamentos/visao-semanal', methods=['GET'])
def agendamentos_visao_semanal():
    """Retorna agendamentos da semana agrupados por laboratório."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    data_ref_str = request.args.get('data_ref')
    try:
        data_ref = datetime.strptime(data_ref_str, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return jsonify({'erro': 'Parâmetro data_ref inválido'}), 400

    inicio_semana = data_ref - timedelta(days=data_ref.weekday())
    fim_semana = inicio_semana + timedelta(days=6)

    query = Agendamento.query.filter(
        Agendamento.data.between(inicio_semana, fim_semana)
    )
    if not verificar_admin(user):
        query = query.filter(Agendamento.usuario_id == user.id)

    agendamentos = query.all()

    resultado = {}
    for a in agendamentos:
        lab = a.laboratorio
        dia = a.data.isoformat()
        turno = a.turno
        resultado.setdefault(lab, {}).setdefault(dia, {}).setdefault(turno, []).append(a.to_dict())

    return jsonify(resultado)


HORARIOS_POR_TURNO = {
    "Manhã": [
        "08:00 - 08:45",
        "08:45 - 09:30",
        "09:30 - 10:15",
        "10:30 - 11:15",
        "11:15 - 12:00",
    ],
    "Tarde": [
        "13:30 - 14:15",
        "14:15 - 15:00",
        "15:00 - 15:45",
        "16:00 - 16:45",
        "16:45 - 17:30",
    ],
    "Noite": [
        "18:30 - 19:15",
        "19:15 - 20:00",
        "20:00 - 20:45",
        "21:00 - 21:45",
        "21:45 - 22:30",
    ],
}


@agendamento_bp.route('/agendamentos/agenda-diaria', methods=['GET'])
def agenda_diaria_laboratorios():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    try:
        laboratorio_id = int(request.args.get('laboratorio_id'))
        data_str = request.args.get('data')
        data_selecionada = datetime.strptime(data_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'erro': 'Parâmetros inválidos ou ausentes'}), 400

    laboratorio_selecionado = db.session.get(Laboratorio, laboratorio_id)
    if not laboratorio_selecionado:
        return jsonify({'erro': 'Laboratório não encontrado'}), 404

    agendamentos = Agendamento.query.filter_by(
        laboratorio=laboratorio_selecionado.nome,
        data=data_selecionada,
    ).all()

    dados_finais = {}

    for turno, horarios_possiveis in HORARIOS_POR_TURNO.items():
        agendamentos_do_turno = [ag for ag in agendamentos if ag.turno == turno]

        horarios_ocupados = set()
        for ag in agendamentos_do_turno:
            horarios_agendados = ag.horarios
            if isinstance(horarios_agendados, str):
                try:
                    horarios_agendados = json.loads(horarios_agendados)
                except json.JSONDecodeError:
                    horarios_agendados = []

            if not isinstance(horarios_agendados, list):
                continue

            for h in horarios_agendados:
                horarios_ocupados.add(h)

        horarios_disponiveis = [h for h in horarios_possiveis if h not in horarios_ocupados]

        dados_finais[turno] = {
            "agendamentos": [
                {
                    "id": ag.id,
                    "turma_nome": ag.turma,
                    "horarios": ag.horarios,
                    "usuario_id": ag.usuario_id,
                }
                for ag in agendamentos_do_turno
            ],
            "horarios_disponiveis": horarios_disponiveis,
        }

    return jsonify(
        {
            "laboratorio_selecionado": laboratorio_selecionado.to_dict(),
            "agendamentos_por_turno": dados_finais,
        }
    )

@agendamento_bp.route('/agendamentos/verificar-disponibilidade', methods=['GET'])
def verificar_disponibilidade():
    """Retorna horários já reservados para um laboratório/data/turno."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    data_str = request.args.get('data')
    laboratorio_nome = request.args.get('laboratorio')
    turno = request.args.get('turno')

    if not all([data_str, laboratorio_nome, turno]):
        return jsonify({'erro': 'Parâmetros incompletos. Forneça data, laboratorio e turno.'}), 400

    try:
        data = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'erro': 'Formato de data inválido. Use YYYY-MM-DD'}), 400

    laboratorio_obj = Laboratorio.query.filter_by(nome=laboratorio_nome).first()

    agendamentos = Agendamento.query.filter(
        Agendamento.data == data,
        Agendamento.laboratorio == laboratorio_nome,
        Agendamento.turno == turno
    ).all()

    horarios_reservados = []
    for ag in agendamentos:
        try:
            hrs = ag.horarios if isinstance(ag.horarios, list) else json.loads(ag.horarios)
            if isinstance(hrs, list):
                horarios_reservados.extend(hrs)
        except Exception:
            pass

    horarios_reservados = sorted(set(horarios_reservados))

    return jsonify({
        'data': data.isoformat(),
        'turno': turno,
        'laboratorio_id': laboratorio_obj.id if laboratorio_obj else None,
        'horarios_reservados': horarios_reservados,
    })


@agendamento_bp.route('/agendamentos/export', methods=['GET'])
def exportar_agendamentos():
    """Exporta agendamentos em CSV, PDF ou XLSX."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    formato = request.args.get('formato', 'csv').lower()

    if verificar_admin(user):
        agendamentos = Agendamento.query.all()
    else:
        agendamentos = Agendamento.query.filter_by(usuario_id=user.id).all()

    if formato == 'pdf':
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(50, 750, "Relatório de Agendamentos")
        y = 730
        c.drawString(50, y, "ID  Usuário  Data  Laboratório  Turma  Turno")
        y -= 20
        for ag in agendamentos:
            nome = ag.usuario.nome if ag.usuario else ''
            c.drawString(50, y, f"{ag.id}  {nome}  {ag.data}  {ag.laboratorio}  {ag.turma}  {ag.turno}")
            y -= 20
            if y < 50:
                c.showPage()
                y = 750
        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name='agendamentos.pdf')

    if formato == 'xlsx':
        wb = Workbook()
        ws = wb.active
        ws.append(["ID", "Nome do Usuário", "Data", "Laboratório", "Turma", "Turno"])
        for ag in agendamentos:
            nome = ag.usuario.nome if ag.usuario else ''
            ws.append([ag.id, nome, ag.data, ag.laboratorio, ag.turma, ag.turno])
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='agendamentos.xlsx'
        )

    # CSV como padrão
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID", "Nome do Usuário", "Data", "Laboratório", "Turma", "Turno"])
    for ag in agendamentos:
        nome = ag.usuario.nome if ag.usuario else ''
        writer.writerow([ag.id, nome, ag.data, ag.laboratorio, ag.turma, ag.turno])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=agendamentos.csv"
    output.headers["Content-Type"] = "text/csv"
    return output

def verificar_conflitos_horarios(data, laboratorio, horarios_list, agendamento_id=None):
    """
    Verifica se há conflitos de horários para um agendamento.
    
    Parâmetros:
        data: Data do agendamento
        laboratorio: Laboratório a ser agendado
        horarios_list: Lista de horários
        agendamento_id: ID do agendamento atual (para excluir da verificação)
        
    Retorna:
        list: Lista de conflitos encontrados
    """
    # Consulta agendamentos no mesmo dia e laboratório
    query = Agendamento.query.filter(
        Agendamento.data == data,
        Agendamento.laboratorio == laboratorio
    )
    
    # Exclui o agendamento atual da verificação (caso seja uma atualização)
    if agendamento_id:
        query = query.filter(Agendamento.id != agendamento_id)
    
    agendamentos_existentes = query.all()
    
    # Se não houver agendamentos no mesmo dia e laboratório, não há conflitos
    if not agendamentos_existentes:
        return []
    
    # Converte os horários do novo agendamento para um conjunto
    try:
        horarios_novos = set(horarios_list)
    except (TypeError, ValueError):
        return ['Formato de horários inválido']
    
    conflitos = []
    
    # Verifica conflitos com cada agendamento existente
    for agendamento in agendamentos_existentes:
        try:
            horarios_existentes = set(agendamento.horarios)
            # Se houver interseção entre os conjuntos de horários, há conflito
            intersecao = horarios_novos.intersection(horarios_existentes)
            if intersecao:
                conflitos.append({
                    'agendamento_id': agendamento.id,
                    'data': agendamento.data.isoformat(),
                    'laboratorio': agendamento.laboratorio,
                    'turma': agendamento.turma,
                    'horarios_conflitantes': list(intersecao)
                })
        except Exception:
            # Ignora agendamentos com formato de horários inválido
            pass
    
    return conflitos


@agendamento_bp.route('/dashboard/laboratorios/kpis', methods=['GET'])
def obter_kpis_dashboard():
    """Retorna contagens gerais para o dashboard de laboratórios."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    total_labs = Laboratorio.query.count()
    total_turmas = Turma.query.count()

    hoje = date.today()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)

    agendamentos_hoje = Agendamento.query.filter(Agendamento.data == hoje).count()
    agendamentos_semana = Agendamento.query.filter(
        Agendamento.data >= inicio_semana,
        Agendamento.data <= fim_semana
    ).count()

    return jsonify({
        'total_laboratorios_ativos': total_labs,
        'total_turmas_ativas': total_turmas,
        'agendamentos_hoje': agendamentos_hoje,
        'agendamentos_semana': agendamentos_semana
    })


@agendamento_bp.route('/dashboard/laboratorios/proximos', methods=['GET'])
def obter_proximos_agendamentos():
    """Retorna os próximos agendamentos (até 10)."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    query = Agendamento.query.filter(Agendamento.data >= date.today())
    if not verificar_admin(user):
        query = query.filter_by(usuario_id=user.id)

    agendamentos = query.order_by(Agendamento.data.asc()).limit(10).all()
    return jsonify([a.to_dict() for a in agendamentos])


@agendamento_bp.route('/dashboard/laboratorios/mais-utilizados', methods=['GET'])
def laboratorios_mais_utilizados():
    """Retorna laboratórios mais agendados no mês atual."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    hoje = date.today()
    inicio_mes = hoje.replace(day=1)
    ultimo_dia = calendar.monthrange(hoje.year, hoje.month)[1]
    fim_mes = date(hoje.year, hoje.month, ultimo_dia)

    resultados = db.session.query(
        Agendamento.laboratorio,
        func.count(Agendamento.id).label('total')
    ).filter(
        Agendamento.data >= inicio_mes,
        Agendamento.data <= fim_mes
    ).group_by(Agendamento.laboratorio)
    resultados = resultados.order_by(func.count(Agendamento.id).desc()).all()

    return jsonify([
        {'laboratorio': lab, 'total': total}
        for lab, total in resultados
    ])


@agendamento_bp.route('/dashboard/laboratorios/tendencia-mensal', methods=['GET'])
def tendencia_mensal_agendamentos():
    """Retorna total de agendamentos por mês do ano atual."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({'erro': 'Não autenticado'}), 401

    ano = date.today().year
    resultados = db.session.query(
        extract('month', Agendamento.data).label('mes'),
        func.count(Agendamento.id).label('total')
    ).filter(
        extract('year', Agendamento.data) == ano
    ).group_by(extract('month', Agendamento.data)).order_by(extract('month', Agendamento.data)).all()

    dados = {int(r.mes): r.total for r in resultados}
    dados_formatados = []
    for m in range(1, 13):
        dados_formatados.append({
            'mes': str(m).zfill(2),
            'total': dados.get(m, 0)
        })

    return jsonify(dados_formatados)
