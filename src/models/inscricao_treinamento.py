from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime
from src.models import db


class InscricaoTreinamento(db.Model):
    __tablename__ = 'inscricoes_treinamento_planejamento'
    id = Column(Integer, primary_key=True)
    treinamento_id = Column(Integer, nullable=True)
    nome_treinamento = Column(String(255), nullable=False)
    matricula = Column(String(50), nullable=False)
    tipo_treinamento = Column(String(100), nullable=False)
    nome_completo = Column(String(255), nullable=False)
    naturalidade = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False)
    data_nascimento = Column(Date, nullable=False)
    cpf = Column(String(14), nullable=False)
    empresa = Column(String(255), nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
