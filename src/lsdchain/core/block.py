"""Estrutura de bloco e hash (SHA-256)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib
import json
import time

from .transaction import Transaction

GENESIS_PREVIOUS_HASH = "0" * 64
GENESIS_HASH = "816534932c2b7154836da6afc367695e6337db8a921823784c14378abed4f7d7"


@dataclass
class Block:
    """Representa um bloco da blockchain."""

    index: int
    previous_hash: str
    transactions: list[Transaction]
    nonce: int = 0
    timestamp: float = field(default_factory=time.time)
    hash: str = ""

    def __post_init__(self) -> None:
        if not self.hash:
            self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        block_data = {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "timestamp": self.timestamp,
        }
        encoded = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Block":
        return cls(
            index=int(data["index"]),
            previous_hash=str(data["previous_hash"]),
            transactions=[Transaction.from_dict(tx) for tx in data["transactions"]],
            nonce=int(data["nonce"]),
            timestamp=float(data["timestamp"]),
            hash=str(data["hash"]),
        )

    @classmethod # decorator de classe, usado para criar o bloco genesis. n precisar de uma instância, chamado diretamente na classe.
    def create_genesis(cls) -> "Block":
        genesis = cls(
            index=0,
            previous_hash=GENESIS_PREVIOUS_HASH,
            transactions=[],
            nonce=0,
            timestamp=0,
        )
        calculated = genesis.calculate_hash()
        if calculated != GENESIS_HASH:
            raise ValueError("Hash do bloco genesis nao confere com o padrao")
        genesis.hash = GENESIS_HASH
        return genesis

    def is_valid_pow(self, difficulty_prefix: str) -> bool:
        return self.hash.startswith(difficulty_prefix)


GENESIS_BLOCK = Block.create_genesis()
