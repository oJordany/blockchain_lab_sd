"""Estrutura de transacao da blockchain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import time
import uuid


@dataclass
class Transaction:
    """Representa uma transacao na blockchain.

    Campos obrigatorios (Padrao Blockchain LSD 2025):
    - id
    - origem
    - destino
    - valor
    - timestamp
    """

    origem: str
    destino: str
    valor: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        # Regras basicas: enderecos obrigatorios e valor positivo.
        if not self.origem or not self.destino:
            raise ValueError("Origem e destino sao obrigatorios")
        if self.valor <= 0:
            raise ValueError("Valor da transacao deve ser positivo")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "origem": self.origem,
            "destino": self.destino,
            "valor": self.valor,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
        return cls(
            id=data["id"],
            origem=data["origem"],
            destino=data["destino"],
            valor=float(data["valor"]),
            timestamp=float(data["timestamp"]),
        )

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Transaction):
            return self.id == other.id
        return False
