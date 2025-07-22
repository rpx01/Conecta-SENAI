"""Inicializacao do pacote de modelos."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .refresh_token import RefreshToken  # noqa: E402
from .recurso import Recurso  # noqa: E402
from .audit_log import AuditLog  # noqa: E402
from .rateio import RateioConfig, LancamentoRateio  # noqa: E402
from .log_rateio import LogLancamentoRateio  # noqa: E402
from .treinamento import Treinamento  # noqa: E402
from .turma_treinamento import TurmaTreinamento  # noqa: E402
from .inscricao_treinamento import InscricaoTreinamento  # noqa: E402

__all__ = [
    "db",
    "RefreshToken",
    "Recurso",
    "AuditLog",
    "RateioConfig",
    "LancamentoRateio",
    "LogLancamentoRateio",
    "Treinamento",
    "TurmaTreinamento",
    "InscricaoTreinamento",
]
