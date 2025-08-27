from enum import Enum as PyEnum
from sqlalchemy import Enum as SAEnum

from . import db


class TurnoEnum(str, PyEnum):
    MANHA = "MANHA"
    TARDE = "TARDE"
    NOITE = "NOITE"
    MANHA_TARDE = "MANHA_TARDE"
    TARDE_NOITE = "TARDE_NOITE"


class Horario(db.Model):
    __tablename__ = "planejamento_horarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    turno = db.Column(
        SAEnum(TurnoEnum, name="turno_enum"), nullable=True, index=True
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "turno": self.turno.name if self.turno else None,
        }
