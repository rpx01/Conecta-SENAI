"""Modelo de horários para base de dados do suporte a treinamentos."""

from __future__ import annotations

from src.models import db


class Horario(db.Model):
    __tablename__ = "horarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    turno = db.Column(db.String(40), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "turno": self.turno,
        }
