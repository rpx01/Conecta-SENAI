"""Inicializacao do pacote de modelos."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .refresh_token import RefreshToken  # noqa: E402
from .recurso import Recurso  # noqa: E402
from .audit_log import AuditLog  # noqa: E402
from .rateio import RateioConfig, LancamentoRateio  # noqa: E402
from .log_rateio import LogLancamentoRateio  # noqa: E402
from .treinamento import (  # noqa: E402
    Treinamento,
    TurmaTreinamento,
    InscricaoTreinamento,
)  # noqa: E402

# Planejamento é um módulo opcional localizado fora do pacote ``src``.
# Em alguns ambientes ele pode não estar instalado no ``PYTHONPATH``,
# o que fazia o Gunicorn falhar ao inicializar.  Realizamos a importação
# de forma defensiva para que a ausência do módulo não interrompa o
# carregamento dos demais modelos.
try:  # pragma: no cover - caminho simples já testado nos imports
    from app.planejamento.models import Planejamento  # noqa: E402
except ImportError:  # pragma: no cover - módulo ausente é aceitável
    Planejamento = None

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

if Planejamento is not None:
    __all__.append("Planejamento")
