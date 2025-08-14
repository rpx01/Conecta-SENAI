from datetime import date

from app import app
from app.extensions import db
from app.planejamento.models import Planejamento
from src.models.instrutor import Instrutor


def run():
    """Cria registros de exemplo para o módulo de planejamento."""
    with app.app_context():
        instrutor = Instrutor(nome="Instrutor Demo")
        db.session.add(instrutor)
        db.session.flush()
        itens = [
            Planejamento(data=date(2024, 1, 10), turno="MANHA", treinamento="Curso A", instrutor_id=instrutor.id),
            Planejamento(data=date(2024, 1, 11), turno="TARDE", treinamento="Curso B", instrutor_id=instrutor.id),
            Planejamento(data=date(2024, 1, 12), turno="NOITE", treinamento="Curso C", instrutor_id=instrutor.id),
        ]
        db.session.add_all(itens)
        db.session.commit()
        print("Planejamentos de exemplo criados.")


if __name__ == "__main__":
    run()
