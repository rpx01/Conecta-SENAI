from flask import g
from sqlalchemy import event
from src.models import db
from src.models.log import Log, LogAcao


def registrar_log(acao, instance, detalhes=None):
    user = getattr(g, 'current_user', None)
    if not user:
        return

    log_entry = Log(
        usuario_id=user.id,
        usuario_nome=user.nome,
        acao=acao,
        modelo_alvo=instance.__class__.__name__,
        id_alvo=getattr(instance, 'id', None),
        detalhes=detalhes or {},
    )
    db.session.add(log_entry)


@event.listens_for(db.session, 'before_flush')
def before_flush(session, flush_context, instances):
    session.info['objetos_antigos'] = {}
    for obj in session.dirty:
        if hasattr(obj, 'id') and obj.id is not None:
            session.info['objetos_antigos'][obj] = db.session.get(obj.__class__, obj.id)


@event.listens_for(db.session, 'after_flush')
def after_flush(session, flush_context):
    for instance in session.new:
        if isinstance(instance, Log):
            continue
        registrar_log(LogAcao.CRIACAO, instance)

    for instance in session.dirty:
        if isinstance(instance, Log):
            continue
        antigo = session.info.get('objetos_antigos', {}).get(instance)
        if not antigo:
            continue
        mudancas = {}
        for attr in db.inspect(instance).attrs.keys():
            valor_antigo = getattr(antigo, attr, None)
            valor_novo = getattr(instance, attr, None)
            if valor_antigo != valor_novo:
                mudancas[attr] = {'de': str(valor_antigo), 'para': str(valor_novo)}
        if mudancas:
            registrar_log(LogAcao.ATUALIZACAO, instance, detalhes=mudancas)

    for instance in session.deleted:
        if isinstance(instance, Log):
            continue
        registrar_log(LogAcao.EXCLUSAO, instance)
