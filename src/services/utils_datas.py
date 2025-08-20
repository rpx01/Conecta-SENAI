# src/services/utils_datas.py
from datetime import date, timedelta

FERIADOS_CMD = {
    # mantenha o mesmo conjunto do front, em ISO 'YYYY-MM-DD'
    date(2025, 1, 1),
    date(2025, 4, 21),
    date(2025, 5, 1),
    date(2025, 9, 7),
    date(2025, 10, 12),
    date(2025, 11, 2),
    date(2025, 11, 15),
    date(2025, 12, 25),
}


def dias_uteis(inicio: date, fim: date):
    d = inicio
    out = []
    while d <= fim:
        # 0=segunda ... 6=domingo
        if d.weekday() < 5 and d not in FERIADOS_CMD:
            out.append(d)
        d += timedelta(days=1)
    return out
