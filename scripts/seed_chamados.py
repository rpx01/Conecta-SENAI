"""Script simples para semear dados do módulo de chamados de TI."""
from __future__ import annotations

import click
from flask import Flask

from src.main import create_app
from src.models import db
from src.models.ticket import TicketCategory, TicketPriority, TicketStatus


@click.command()
def seed_chamados() -> None:
    """Popula categorias, prioridades e status padrão."""
    app: Flask = create_app()
    with app.app_context():
        dados = [
            (TicketCategory, {"nome": "Suporte", "descricao": "Suporte geral"}),
            (TicketCategory, {"nome": "Infraestrutura", "descricao": "Rede e servidores"}),
            (TicketPriority, {"nome": "baixa", "peso": 1}),
            (TicketPriority, {"nome": "media", "peso": 2}),
            (TicketPriority, {"nome": "alta", "peso": 3}),
            (TicketPriority, {"nome": "critica", "peso": 4}),
            (TicketStatus, {"nome": "aberto", "ordem": 1}),
            (TicketStatus, {"nome": "em_atendimento", "ordem": 2}),
            (TicketStatus, {"nome": "pendente", "ordem": 3}),
            (TicketStatus, {"nome": "resolvido", "ordem": 4}),
            (TicketStatus, {"nome": "fechado", "ordem": 5}),
        ]
        for modelo, valores in dados:
            existente = modelo.query.filter_by(nome=valores["nome"]).first()
            if not existente:
                db.session.add(modelo(**valores))
        db.session.commit()
        click.echo('Dados de chamados inseridos com sucesso.')


if __name__ == '__main__':
    seed_chamados()
