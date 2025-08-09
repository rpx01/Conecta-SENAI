"""Tarefas assíncronas executadas via RQ."""
from io import BytesIO
import csv
from typing import List, Dict, Tuple

from src.redis_client import redis_conn, DummyRedis

try:  # pragma: no cover - falha se RQ não estiver disponível
    from rq import Queue
except Exception:  # pragma: no cover
    Queue = None

queue = None


def init_task_queue():
    """Inicializa a fila de tarefas com a conexão Redis atual."""
    global queue
    if Queue is None or isinstance(redis_conn, DummyRedis):
        queue = None
    else:  # pragma: no branch - simples inicialização
        queue = Queue(connection=redis_conn)
    return queue


# Inicializa a fila ao importar, se possível
init_task_queue()


def gerar_relatorio_agendamentos(formato: str, agendamentos: List[Dict]) -> Tuple[bytes, str, str]:
    """Gera relatório de agendamentos no formato solicitado."""
    if formato == 'pdf':
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(50, 750, "Relatório de Agendamentos")
        y = 730
        c.drawString(50, y, "ID  Usuário  Data  Laboratório  Turma  Turno")
        y -= 20
        for ag in agendamentos:
            c.drawString(50, y, f"{ag['id']}  {ag.get('usuario', '')}  {ag['data']}  {ag['laboratorio']}  {ag['turma']}  {ag['turno']}")
            y -= 20
            if y < 50:
                c.showPage()
                y = 750
        c.save()
        buffer.seek(0)
        return buffer.getvalue(), 'application/pdf', 'agendamentos.pdf'

    if formato == 'xlsx':
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.append(['ID', 'Usuário', 'Data', 'Laboratório', 'Turma', 'Turno'])
        for ag in agendamentos:
            ws.append([ag['id'], ag.get('usuario', ''), ag['data'], ag['laboratorio'], ag['turma'], ag['turno']])
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'agendamentos.xlsx'

    # CSV padrão
    from io import StringIO

    text_buffer = StringIO()
    writer = csv.writer(text_buffer, delimiter=';')
    writer.writerow(['ID', 'Usuário', 'Data', 'Laboratório', 'Turma', 'Turno'])
    for ag in agendamentos:
        writer.writerow([ag['id'], ag.get('usuario', ''), ag['data'], ag['laboratorio'], ag['turma'], ag['turno']])
    data = text_buffer.getvalue().encode('utf-8')
    return data, 'text/csv', 'agendamentos.csv'

