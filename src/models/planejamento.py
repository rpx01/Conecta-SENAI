"""Model for storing planning items."""
from datetime import datetime
from src.models import db


class PlanejamentoItem(db.Model):
    """Representa uma linha de planejamento trimestral."""
    __tablename__ = "planejamento_itens"

    id = db.Column(db.Integer, primary_key=True)
    row_id = db.Column(db.String(36), unique=True, nullable=False)
    lote_id = db.Column(db.String(36), nullable=False)
    data = db.Column(db.Date, nullable=False)
    semana = db.Column(db.String(20))
    horario = db.Column(db.String(50))
    carga_horaria = db.Column(db.String(50))
    modalidade = db.Column(db.String(50))
    treinamento = db.Column(db.String(100))
    cmd = db.Column(db.String(100))
    sjb = db.Column(db.String(100))
    sag_tombos = db.Column(db.String(100))
    instrutor = db.Column(db.String(100))
    local = db.Column(db.String(100))
    observacao = db.Column(db.String(255))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        """Converte o item para dicionário."""
        return {
            "id": self.id,
            "rowId": self.row_id,
            "loteId": self.lote_id,
            "data": self.data.isoformat() if self.data else None,
            "semana": self.semana,
            "horario": self.horario,
            "cargaHoraria": self.carga_horaria,
            "modalidade": self.modalidade,
            "treinamento": self.treinamento,
            "cmd": self.cmd,
            "sjb": self.sjb,
            "sagTombos": self.sag_tombos,
            "instrutor": self.instrutor,
            "local": self.local,
            "observacao": self.observacao,
            "criadoEm": (
                self.criado_em.isoformat() if self.criado_em else None
            ),
            "atualizadoEm": (
                self.atualizado_em.isoformat() if self.atualizado_em else None
            ),
        }
