"""Definições de fila e tarefas assíncronas."""
from io import BytesIO, StringIO
import csv
from rq import Queue
from src.redis_client import redis_conn, DummyRedis

# Inicializa fila apenas se Redis estiver disponível
if isinstance(redis_conn, DummyRedis):
    task_queue = None
else:
    task_queue = Queue(connection=redis_conn)

def exportar_agendamentos_task(formato: str, agendamentos: list[dict]):
    """Gera arquivos de exportação de agendamentos."""
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
            c.drawString(50, y, f"{ag['id']}  {ag['usuario']}  {ag['data']}  {ag['laboratorio']}  {ag['turma']}  {ag['turno']}")
            y -= 20
            if y < 50:
                c.showPage()
                y = 750
        c.save()
        return {
            'data': buffer.getvalue(),
            'mimetype': 'application/pdf',
            'filename': 'agendamentos.pdf'
        }
    if formato == 'xlsx':
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.append(["ID", "Nome do Usuário", "Data", "Laboratório", "Turma", "Turno"])
        for ag in agendamentos:
            ws.append([ag['id'], ag['usuario'], ag['data'], ag['laboratorio'], ag['turma'], ag['turno']])
        output = BytesIO()
        wb.save(output)
        return {
            'data': output.getvalue(),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'filename': 'agendamentos.xlsx'
        }
    # CSV como padrão
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID", "Nome do Usuário", "Data", "Laboratório", "Turma", "Turno"])
    for ag in agendamentos:
        writer.writerow([ag['id'], ag['usuario'], ag['data'], ag['laboratorio'], ag['turma'], ag['turno']])
    return {
        'data': si.getvalue().encode('utf-8'),
        'mimetype': 'text/csv',
        'filename': 'agendamentos.csv'
    }
