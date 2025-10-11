from datetime import datetime, timedelta, timezone

from src.models import db
from src.models.noticia import Noticia


def _parse_iso_datetime(value: str) -> datetime:
    if value.endswith('Z'):
        value = value[:-1] + '+00:00'
    return datetime.fromisoformat(value)


def test_listar_noticias_calendario_retorna_apenas_publicadas(app, client):
    with app.app_context():
        base = datetime.now(timezone.utc)
        noticia_visivel_1 = Noticia(
            titulo="Evento no calendário",
            conteudo="Conteúdo",
            marcar_calendario=True,
            data_evento=base + timedelta(days=1),
        )
        noticia_visivel_2 = Noticia(
            titulo="Evento futuro",
            conteudo="Conteúdo",
            marcar_calendario=True,
            data_evento=base + timedelta(days=5),
        )
        noticia_inativa = Noticia(
            titulo="Inativa",
            conteudo="Conteúdo",
            marcar_calendario=True,
            ativo=False,
            data_evento=base + timedelta(days=2),
        )
        noticia_sem_data = Noticia(
            titulo="Sem data",
            conteudo="Conteúdo",
            marcar_calendario=True,
            data_evento=None,
        )
        noticia_nao_marcada = Noticia(
            titulo="Fora do calendário",
            conteudo="Conteúdo",
            marcar_calendario=False,
            data_evento=base + timedelta(days=3),
        )
        db.session.add_all(
            [
                noticia_visivel_1,
                noticia_visivel_2,
                noticia_inativa,
                noticia_sem_data,
                noticia_nao_marcada,
            ]
        )
        db.session.commit()

        ids_esperados = [noticia_visivel_1.id, noticia_visivel_2.id]
        titulos_esperados = [noticia_visivel_1.titulo, noticia_visivel_2.titulo]
        datas_esperadas = [
            noticia_visivel_1.data_evento,
            noticia_visivel_2.data_evento,
        ]

    response = client.get('/api/noticias/calendario')

    assert response.status_code == 200
    eventos = response.get_json()
    assert isinstance(eventos, list)
    assert [evento['id'] for evento in eventos] == ids_esperados
    assert [evento['titulo'] for evento in eventos] == titulos_esperados

    datas_retorno = [_parse_iso_datetime(evento['data_evento']) for evento in eventos]
    assert datas_retorno == datas_esperadas
