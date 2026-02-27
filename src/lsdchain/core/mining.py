"""Mineracao (Proof of Work simplificado)."""

from __future__ import annotations

import time
from typing import Callable

from .block import Block
from .blockchain import Blockchain, COINBASE_REWARD, COINBASE_SENDER, DIFFICULTY_PREFIX
from .transaction import Transaction


class Miner:
    """Minerador que procura um nonce com hash iniciando em '000'."""

    def __init__(self, blockchain: Blockchain, miner_address: str) -> None:
        self.blockchain = blockchain
        self.miner_address = miner_address
        self._mining = False

    def mine_block(
        self,
        transactions: list[Transaction] | None = None,
        on_progress: Callable[[int], None] | None = None,
    ) -> Block | None:
        if transactions is None:
            transactions = list(self.blockchain.pending_transactions)

        # Coinbase: primeira transacao do bloco, cria novas moedas.
        block_timestamp = time.time()
        reward_tx = Transaction(
            origem=COINBASE_SENDER,
            destino=self.miner_address,
            valor=COINBASE_REWARD,
            timestamp=block_timestamp,
        )
        block_transactions = [reward_tx] + transactions

        # Bloco candidato; o nonce sera ajustado ate satisfazer o PoW.
        block = Block(
            index=len(self.blockchain.chain),
            previous_hash=self.blockchain.last_block.hash,
            transactions=block_transactions,
            nonce=0,
            timestamp=block_timestamp,
        )

        self._mining = True
        while self._mining:
            block.hash = block.calculate_hash()
            if block.is_valid_pow(DIFFICULTY_PREFIX):
                self._mining = False
                return block
            block.nonce += 1
            if on_progress and block.nonce % 10000 == 0:
                on_progress(block.nonce)
        return None

    def stop(self) -> None:
        self._mining = False
