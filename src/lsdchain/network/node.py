"""No da rede P2P, comunicacao via sockets (TCP)."""

from __future__ import annotations

import logging
import socket
import threading
from typing import Any

from ..core.block import Block
from ..core.blockchain import Blockchain
from ..core.mining import Miner
from ..core.transaction import Transaction
from .protocol import Message, MessageType, Protocol


LOGGER_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def _read_exact(sock: socket.socket, size: int) -> bytes:
    """Le exatamente `size` bytes do socket ou encerra se a conexao fechar."""
    data = b""
    # recv() pode retornar menos bytes do que o pedido, por isso acumulamos.
    while len(data) < size:
        # sock.recv(n) bloqueia ate receber dados ou a conexao fechar.
        chunk = sock.recv(size - len(data))
        # Se recv retornar vazio, a outra ponta encerrou a conexao.
        if not chunk:
            break
        data += chunk
    return data


class Node:
    """Representa um no da rede da blockchain."""

    BUFFER_SIZE = 64 * 1024

    def __init__(self, host: str, port: int) -> None:
        """Inicializa o no com endereco local e estruturas internas."""
        self.host = host
        self.port = port
        self.address = f"{host}:{port}"

        # Cada no possui sua propria blockchain e minerador local.
        self.blockchain = Blockchain()
        self.miner = Miner(self.blockchain, self.address)

        # Lista de peers conhecidos e estado do servidor.
        self.peers: set[str] = set()
        self._server: socket.socket | None = None
        self._running = False

        # Logger para acompanhar eventos do no.
        logging.basicConfig(level=logging.INFO, format=LOGGER_FORMAT)
        self.logger = logging.getLogger(f"Node:{self.port}")

    def start(self) -> None:
        """Inicia o servidor TCP e a thread de aceitacao de conexoes."""
        # socket(AF_INET, SOCK_STREAM) => TCP/IPv4.
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # SO_REUSEADDR permite reutilizar a porta rapidamente apos fechar.
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # bind() associa o socket ao endereco local (host:porta).
        self._server.bind((self.host, self.port))
        # listen() coloca o socket em modo servidor (fila/backlog = 20).
        self._server.listen(20)
        self._running = True
        self.logger.info("No iniciado em %s", self.address)

        # Thread separada para aceitar conexoes sem travar o processo.
        thread = threading.Thread(target=self._accept_loop, daemon=True)
        thread.start()

    def stop(self) -> None:
        """Encerra o servidor TCP e interrompe a mineracao."""
        # Encerra loop e mineracao; fecha o socket servidor.
        self._running = False
        self.miner.stop()
        if self._server:
            self._server.close()
        self.logger.info("No encerrado")

    def _accept_loop(self) -> None:
        """Loop interno que aceita conexoes de clientes."""
        while self._running:
            try:
                # accept() bloqueia ate chegar uma conexao; retorna o socket do cliente.
                client_socket, _ = self._server.accept()
                # Trata cada cliente em thread separada para nao bloquear novas conexoes.
                thread = threading.Thread(
                    target=self._handle_client, args=(client_socket,), daemon=True
                )
                thread.start()
            except Exception as exc:
                if self._running:
                    self.logger.error("Erro ao aceitar conexao: %s", exc)

    def _handle_client(self, client_socket: socket.socket) -> None:
        """Processa uma conexao: le mensagem, trata e responde."""
        try:
            # Le o tamanho (4 bytes) e depois o JSON da mensagem.
            length_raw = _read_exact(client_socket, 4)
            if not length_raw:
                return
            length = int.from_bytes(length_raw, "big")
            # sock.recv dentro de _read_exact garante leitura completa do corpo.
            body = _read_exact(client_socket, length)
            if not body:
                return

            # Processa a mensagem e gera resposta (quando necessario).
            message = Message.from_bytes(body)
            response = self._process_message(message)
            if response:
                response.sender = self.address
                # sendall() envia todos os bytes da resposta.
                client_socket.sendall(response.to_bytes())
        except Exception as exc:
            self.logger.error("Erro ao processar cliente: %s", exc)
        finally:
            # close() encerra a conexao com o cliente.
            client_socket.close()

    def _process_message(self, message: Message) -> Message | None:
        """Roteia o tratamento conforme o tipo de mensagem do protocolo."""
        # Centraliza o tratamento de mensagens do protocolo.
        self.logger.info("Mensagem %s de %s", message.type.value, message.sender)
        if message.sender and message.sender != self.address:
            self.peers.add(message.sender)

        if message.type == MessageType.NEW_TRANSACTION:
            # Transacao recebida: valida, adiciona e propaga.
            tx_data = message.payload.get("transaction", {})
            try:
                transaction = Transaction.from_dict(tx_data)
            except Exception as exc:
                self.logger.warning("Transacao invalida recebida: %s", exc)
                return None
            if self.blockchain.add_transaction(transaction):
                self.logger.info("Transacao adicionada: %s", transaction.id)
                # _broadcast cria threads para enviar aos peers.
                self._broadcast(
                    Protocol.new_transaction(transaction.to_dict()),
                    exclude=message.sender,
                )

        elif message.type == MessageType.NEW_BLOCK:
            # Bloco recebido: valida, adiciona e propaga.
            block_data = message.payload.get("block", {})
            try:
                block = Block.from_dict(block_data)
            except Exception as exc:
                self.logger.warning("Bloco invalido recebido: %s", exc)
                return None
            if self.blockchain.add_block(block):
                self.logger.info("Bloco #%s adicionado", block.index)
                self.miner.stop()
                self._broadcast(
                    Protocol.new_block(block.to_dict()),
                    exclude=message.sender,
                )

        elif message.type == MessageType.REQUEST_CHAIN:
            # Envia a cadeia completa para sincronizacao.
            return Protocol.response_chain(self.blockchain.to_dict())

        elif message.type == MessageType.RESPONSE_CHAIN:
            # Recebe cadeia de outro no e troca se for maior e valida.
            chain_data = message.payload.get("blockchain", {})
            new_chain = [Block.from_dict(b) for b in chain_data.get("chain", [])]
            new_pending = [
                Transaction.from_dict(tx)
                for tx in chain_data.get("pending_transactions", [])
            ]
            if self.blockchain.replace_chain(new_chain):
                self.blockchain.pending_transactions = new_pending
                self.logger.info(
                    "Blockchain atualizada (%s blocos)", len(self.blockchain.chain)
                )

        return None

    def _send_message(
        self, peer: str, message: Message, expect_response: bool = False
    ) -> Message | None:
        """Envia mensagem a um peer e (opcionalmente) aguarda resposta."""
        try:
            host, port = peer.split(":")
            # Cria socket cliente TCP e conecta no peer.
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                # settimeout() evita bloqueio infinito em rede.
                sock.settimeout(10)
                # connect() abre conexao TCP com o peer.
                sock.connect((host, int(port)))
                message.sender = self.address
                # sendall() envia mensagem completa com framing.
                sock.sendall(message.to_bytes())

                if not expect_response:
                    return None
                # Se esperado, le a resposta com o mesmo framing.
                length_raw = _read_exact(sock, 4)
                if not length_raw:
                    return None
                length = int.from_bytes(length_raw, "big")
                # recv() dentro de _read_exact le o corpo completo.
                body = _read_exact(sock, length)
                if not body:
                    return None
                return Message.from_bytes(body)
        except Exception as exc:
            self.logger.error("Erro ao enviar para %s: %s", peer, exc)
            return None

    def _broadcast(self, message: Message, exclude: str | None = None) -> None:
        """Propaga uma mensagem para todos os peers conhecidos."""
        # Envia para todos os peers conhecidos, exceto o remetente.
        for peer in list(self.peers):
            if exclude and peer == exclude:
                continue
            # Cada envio roda em thread para nao bloquear.
            thread = threading.Thread(
                target=self._send_message,
                args=(peer, message, False),
                daemon=True,
            )
            thread.start()

    def connect_to_peer(self, peer: str) -> bool:
        """Conecta a um peer e sincroniza a blockchain a partir dele."""
        if peer == self.address:
            return False
        # Conecta e solicita a cadeia para sincronizar.
        response = self._send_message(peer, Protocol.request_chain(), True)
        if response and response.type == MessageType.RESPONSE_CHAIN:
            self.peers.add(peer)
            self._process_message(response)
            return True
        return False

    def sync_blockchain(self) -> None:
        """Solicita a blockchain aos peers para sincronizar."""
        # Pede cadeia a cada peer e aplica a maior valida.
        for peer in list(self.peers):
            response = self._send_message(peer, Protocol.request_chain(), True)
            if response and response.type == MessageType.RESPONSE_CHAIN:
                self._process_message(response)

    def broadcast_transaction(self, transaction: Transaction) -> bool:
        """Adiciona transacao local e propaga para os peers."""
        # Adiciona no pool local e propaga.
        if not self.blockchain.add_transaction(transaction):
            return False
        self._broadcast(Protocol.new_transaction(transaction.to_dict()))
        return True

    def broadcast_block(self, block: Block) -> bool:
        """Adiciona bloco local e propaga para os peers."""
        # Adiciona o bloco localmente e propaga.
        if not self.blockchain.add_block(block):
            return False
        self._broadcast(Protocol.new_block(block.to_dict()))
        return True

    def mine(self) -> Block | None:
        """Executa a mineracao e propaga o bloco se for valido."""
        self.logger.info("Mineracao iniciada")
        # Minera um novo bloco com as pendentes atuais.
        block = self.miner.mine_block()
        if block:
            self.logger.info("Bloco minerado #%s", block.index)
            self.broadcast_block(block)
        return block
