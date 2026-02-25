"""Gerenciamento da blockchain e das transacoes pendentes."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .block import Block, GENESIS_HASH, GENESIS_PREVIOUS_HASH
from .transaction import Transaction

DIFFICULTY_PREFIX = "000"
COINBASE_SENDER = "coinbase"
COINBASE_REWARD = 50.0


class Blockchain:
    """Mantem a cadeia de blocos e o pool de transacoes pendentes."""

    def __init__(self) -> None:
        self.chain: list[Block] = [Block.create_genesis()]
        self.pending_transactions: list[Transaction] = []

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def get_balance(self, address: str) -> float:
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.destino == address:
                    balance += tx.valor
                if tx.origem == address:
                    balance -= tx.valor
        for tx in self.pending_transactions:
            if tx.destino == address:
                balance += tx.valor
            if tx.origem == address:
                balance -= tx.valor
        return balance

    def _get_chain_balances(self, target_chain: list[Block] | None = None) -> dict[str, float]:
        if target_chain is None:
            target_chain = self.chain
                    
        balances: dict[str, float] = defaultdict(float)
        for block in target_chain:
            for tx in block.transactions:
                balances[tx.destino] += tx.valor
                balances[tx.origem] -= tx.valor
            return balances

    def add_transaction(self, transaction: Transaction) -> bool:
        if self._is_duplicate(transaction):
            return False
        if not self._validate_transaction_basic(transaction):
            return False
        if transaction.origem == COINBASE_SENDER:
            return False
        if transaction.origem not in (COINBASE_SENDER, "genesis"):
            if self.get_balance(transaction.origem) < transaction.valor:
                return False
        self.pending_transactions.append(transaction)
        return True

    def _is_duplicate(self, transaction: Transaction) -> bool:
        for tx in self.pending_transactions:
            if tx.id == transaction.id:
                return True
        for block in self.chain:
            for tx in block.transactions:
                if tx.id == transaction.id:
                    return True
        return False

    def _validate_transaction_basic(self, transaction: Transaction) -> bool:
        try:
            return transaction.valor > 0 and transaction.origem and transaction.destino
        except Exception:
            return False

    def add_block(self, block: Block) -> bool:
        if not self.is_valid_block(block):
            return False

        included_ids = {tx.id for tx in block.transactions}
        self.pending_transactions = [
            tx for tx in self.pending_transactions if tx.id not in included_ids
        ]
        self.chain.append(block)
        return True

    def is_valid_block(self, block: Block) -> bool:
        if block.index != len(self.chain):
            return False
        if block.previous_hash != self.last_block.hash:
            return False
        if block.hash != block.calculate_hash():
            return False
        if not block.is_valid_pow(DIFFICULTY_PREFIX):
            return False
        if not self._validate_block_transactions(block):
            return False
        return True

    def _validate_block_transactions(self, block: Block, target_chain: list[Block] | None = None) -> bool:
        if not block.transactions:
            return False

        first = block.transactions[0]
        if first.origem != COINBASE_SENDER:
            return False
        if first.valor != COINBASE_REWARD:
            return False
        if first.timestamp != block.timestamp:
            return False

        balances = self._get_chain_balances(target_chain)
        for idx, tx in enumerate(block.transactions):
            if not self._validate_transaction_basic(tx):
                return False
            if idx == 0 and tx.origem == COINBASE_SENDER:
                balances[tx.destino] += tx.valor
                continue
            if tx.origem == COINBASE_SENDER:
                return False
            if balances[tx.origem] < tx.valor:
                return False
            balances[tx.origem] -= tx.valor
            balances[tx.destino] += tx.valor
        return True

    def is_valid_chain(self, chain: list[Block]) -> bool:
        if not chain:
            return False
        genesis = chain[0]
        if (
            genesis.index != 0
            or genesis.previous_hash != GENESIS_PREVIOUS_HASH
            or genesis.hash != GENESIS_HASH
            or genesis.timestamp != 0
            or genesis.nonce != 0
            or genesis.transactions
        ):
            return False
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i - 1]
            if current.index != i:
                return False
            if current.previous_hash != previous.hash:
                return False
            if current.hash != current.calculate_hash():
                return False
            if not current.is_valid_pow(DIFFICULTY_PREFIX):
                return False
            if not self._validate_block_transactions(current, target_chain=chain[:i]):
                return False
        return True

    def replace_chain(self, new_chain: list[Block]) -> bool:
        if len(new_chain) <= len(self.chain):
            return False
        if not self.is_valid_chain(new_chain):
            return False
        self.chain = new_chain
        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Blockchain":
        instance = cls()
        instance.chain = [Block.from_dict(b) for b in data["chain"]]
        instance.pending_transactions = [
            Transaction.from_dict(tx) for tx in data["pending_transactions"]
        ]
        return instance
