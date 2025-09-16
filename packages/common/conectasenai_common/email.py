"""Utilidades genéricas para envio de e-mails."""
from __future__ import annotations

import re
import threading
import time as time_module
from collections import deque
from datetime import time
from types import SimpleNamespace
from typing import Any, Callable, Iterable, List, Optional, Union

Address = Union[str, Iterable[str]]


class RateLimiter:
    """Decorator que limita a taxa de execução de uma função."""

    def __init__(self, max_calls: int, period: int = 1) -> None:
        self.calls: deque[float] = deque()
        self.period = period
        self.max_calls = max_calls
        self.lock = threading.Lock()

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with self.lock:
                now = time_module.monotonic()
                while self.calls and now - self.calls[0] >= self.period:
                    self.calls.popleft()

                if len(self.calls) >= self.max_calls:
                    sleep_for = (self.calls[0] + self.period) - now
                    if sleep_for > 0:
                        time_module.sleep(sleep_for)
                        now = time_module.monotonic()
                        while self.calls and now - self.calls[0] >= self.period:
                            self.calls.popleft()

                self.calls.append(time_module.monotonic())

            return func(*args, **kwargs)

        return wrapper


def normalize_addresses(addr: Address | None) -> Optional[List[str]]:
    """Normaliza entradas de e-mail para sempre retornar uma lista."""
    if addr is None:
        return None
    if isinstance(addr, str):
        return [addr]
    return list(addr)


def parse_time(value: Any) -> time | None:
    """Converte representações diversas de horário em ``datetime.time``."""
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        digits = [int(x) for x in re.findall(r"\d+", value)]
        if digits:
            hour = digits[0]
            minute = digits[1] if len(digits) > 1 else 0
            try:
                return time(hour, minute)
            except ValueError:
                return None
    return None


def build_turma_context(turma: Any) -> SimpleNamespace:
    """Gera um contexto serializável com dados essenciais da turma."""
    treino = getattr(turma, "treinamento", None)
    return SimpleNamespace(
        treinamento=SimpleNamespace(nome=getattr(treino, "nome", "")),
        nome=getattr(turma, "nome", ""),
        instrutor=getattr(turma, "instrutor", None),
        data_inicio=getattr(turma, "data_inicio", None),
        data_termino=getattr(turma, "data_fim", None),
        horario_inicio=parse_time(
            getattr(turma, "horario_inicio", getattr(turma, "horario", None))
        )
        or time(0, 0),
        horario_fim=parse_time(
            getattr(turma, "horario_fim", getattr(turma, "horario", None))
        )
        or time(0, 0),
        local=getattr(turma, "local", getattr(turma, "local_realizacao", "")),
        capacidade_maxima=getattr(turma, "capacidade_maxima", None),
    )


def build_user_context(nome: str) -> SimpleNamespace:
    """Cria um contexto simples para representar um usuário."""
    return SimpleNamespace(name=nome)


__all__ = [
    "Address",
    "RateLimiter",
    "normalize_addresses",
    "parse_time",
    "build_turma_context",
    "build_user_context",
]
