"""Interface grafica (Tkinter) para o no da blockchain."""

from __future__ import annotations

import threading
import time
import tkinter as tk
from tkinter import ttk

from ..core.transaction import Transaction
from ..core.validation import is_host_port_address
from ..network.node import Node


class BlockchainApp:
    """Aplicacao Tkinter para operar o no."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Blockchain LSD 2025")
        self.node: Node | None = None

        self.host_var = tk.StringVar(value="127.0.0.1")
        self.port_var = tk.StringVar(value="5000")
        self.bootstrap_var = tk.StringVar(value="")

        self.tx_from_var = tk.StringVar()
        self.tx_to_var = tk.StringVar()
        self.tx_value_var = tk.StringVar()
        self.balance_addr_var = tk.StringVar()
        self.peer_var = tk.StringVar()

        self._build_layout()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)

        config_frame = ttk.LabelFrame(self.root, text="Configuracao do No")
        config_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=6)
        config_frame.columnconfigure(5, weight=1)

        ttk.Label(config_frame, text="Host").grid(row=0, column=0, padx=4, pady=4)
        ttk.Entry(config_frame, textvariable=self.host_var, width=16).grid(
            row=0, column=1, padx=4, pady=4
        )
        ttk.Label(config_frame, text="Porta").grid(row=0, column=2, padx=4, pady=4)
        ttk.Entry(config_frame, textvariable=self.port_var, width=8).grid(
            row=0, column=3, padx=4, pady=4
        )
        ttk.Label(config_frame, text="Bootstrap(s)").grid(
            row=0, column=4, padx=4, pady=4
        )
        ttk.Entry(config_frame, textvariable=self.bootstrap_var, width=32).grid(
            row=0, column=5, padx=4, pady=4, sticky="ew"
        )
        self.start_button = ttk.Button(
            config_frame, text="Iniciar No", command=self._start_node
        )
        self.start_button.grid(row=0, column=6, padx=6, pady=4)

        tx_frame = ttk.LabelFrame(self.root, text="Transacao")
        tx_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=6)
        for i in range(7):
            tx_frame.columnconfigure(i, weight=1)

        ttk.Label(tx_frame, text="Origem").grid(row=0, column=0, padx=4, pady=4)
        ttk.Entry(tx_frame, textvariable=self.tx_from_var).grid(
            row=0, column=1, padx=4, pady=4, sticky="ew"
        )
        ttk.Label(tx_frame, text="Destino").grid(row=0, column=2, padx=4, pady=4)
        ttk.Entry(tx_frame, textvariable=self.tx_to_var).grid(
            row=0, column=3, padx=4, pady=4, sticky="ew"
        )
        ttk.Label(tx_frame, text="Valor").grid(row=0, column=4, padx=4, pady=4)
        ttk.Entry(tx_frame, textvariable=self.tx_value_var, width=10).grid(
            row=0, column=5, padx=4, pady=4
        )
        ttk.Button(tx_frame, text="Enviar", command=self._create_transaction).grid(
            row=0, column=6, padx=4, pady=4
        )

        actions_frame = ttk.LabelFrame(self.root, text="Acoes")
        actions_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=6)
        for i in range(5):
            actions_frame.columnconfigure(i, weight=1)

        self.mine_button = ttk.Button(
            actions_frame, text="Minerar", command=self._mine_block, state="disabled"
        )
        self.mine_button.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        self.pending_button = ttk.Button(
            actions_frame,
            text="Pendentes",
            command=self._show_pending,
            state="disabled",
        )
        self.pending_button.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        self.chain_button = ttk.Button(
            actions_frame,
            text="Blockchain",
            command=self._show_blockchain,
            state="disabled",
        )
        self.chain_button.grid(row=0, column=2, padx=4, pady=4, sticky="ew")
        self.sync_button = ttk.Button(
            actions_frame,
            text="Sincronizar",
            command=self._sync_chain,
            state="disabled",
        )
        self.sync_button.grid(row=0, column=3, padx=4, pady=4, sticky="ew")
        self.peers_button = ttk.Button(
            actions_frame,
            text="Peers",
            command=self._show_peers,
            state="disabled",
        )
        self.peers_button.grid(row=0, column=4, padx=4, pady=4, sticky="ew")

        peer_frame = ttk.LabelFrame(self.root, text="Peer Manual")
        peer_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=6)
        peer_frame.columnconfigure(1, weight=1)

        ttk.Label(peer_frame, text="Endereco").grid(row=0, column=0, padx=4, pady=4)
        ttk.Entry(peer_frame, textvariable=self.peer_var).grid(
            row=0, column=1, padx=4, pady=4, sticky="ew"
        )
        self.connect_button = ttk.Button(
            peer_frame, text="Conectar", command=self._connect_peer, state="disabled"
        )
        self.connect_button.grid(row=0, column=2, padx=4, pady=4)

        balance_frame = ttk.LabelFrame(self.root, text="Consultar Saldo")
        balance_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=6)
        balance_frame.columnconfigure(1, weight=1)

        ttk.Label(balance_frame, text="Endereco").grid(
            row=0, column=0, padx=4, pady=4
        )
        ttk.Entry(balance_frame, textvariable=self.balance_addr_var).grid(
            row=0, column=1, padx=4, pady=4, sticky="ew"
        )
        ttk.Button(balance_frame, text="Consultar", command=self._show_balance).grid(
            row=0, column=2, padx=4, pady=4
        )

        log_frame = ttk.LabelFrame(self.root, text="Log")
        log_frame.grid(row=5, column=0, sticky="nsew", padx=10, pady=6)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=16, wrap="word")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _set_actions_state(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.mine_button.configure(state=state)
        self.pending_button.configure(state=state)
        self.chain_button.configure(state=state)
        self.sync_button.configure(state=state)
        self.peers_button.configure(state=state)
        self.connect_button.configure(state=state)

    def _log(self, message: str) -> None:
        def append() -> None:
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")

        self.root.after(0, append)

    def _start_node(self) -> None:
        if self.node:
            self._log("No ja iniciado.")
            return
        host = self.host_var.get().strip() or "127.0.0.1"
        try:
            port = int(self.port_var.get().strip())
        except ValueError:
            self._log("Porta invalida.")
            return

        # Cria o no local e inicia o servidor TCP.
        self.node = Node(host=host, port=port)
        self.node.start()
        self._log(f"No iniciado em {host}:{port}")
        self.start_button.configure(state="disabled")
        self._set_actions_state(True)

        # Conecta em bootstrap(s) para descobrir/sincronizar a blockchain.
        bootstrap_raw = self.bootstrap_var.get().strip()
        if bootstrap_raw:
            for peer in self._parse_peers(bootstrap_raw):
                if not is_host_port_address(peer):
                    self._log(f"Bootstrap invalido: {peer}")
                    continue
                if self.node.connect_to_peer(peer):
                    self._log(f"Conectado ao bootstrap {peer}")

        # Se houver peers, pede a cadeia e sincroniza.
        if self.node.peers:
            self._log("Sincronizando blockchain...")
            self.node.sync_blockchain()
            self._log(f"Blockchain com {len(self.node.blockchain.chain)} blocos")

    def _parse_peers(self, raw: str) -> list[str]:
        parts = [item.strip() for item in raw.replace(";", ",").split(",")]
        return [item for item in parts if item]

    def _create_transaction(self) -> None:
        if not self.node:
            self._log("Inicie o no primeiro.")
            return
        origem = self.tx_from_var.get().strip()
        destino = self.tx_to_var.get().strip()
        if not is_host_port_address(origem) or not is_host_port_address(destino):
            self._log("Endereco invalido. Use o formato host:porta.")
            return
        try:
            valor = float(self.tx_value_var.get().strip())
        except ValueError:
            self._log("Valor invalido.")
            return
        try:
            tx = Transaction(origem=origem, destino=destino, valor=valor)
        except ValueError as exc:
            self._log(f"Erro: {exc}")
            return
        if origem not in ("genesis", "coinbase"):
            saldo = self.node.blockchain.get_balance(origem)
            if saldo < valor:
                self._log(f"Saldo insuficiente: {saldo} < {valor}")
                return
        # Adiciona no pool local e propaga para os peers.
        if self.node.broadcast_transaction(tx):
            self._log(f"Transacao enviada: {tx.id}")
        else:
            self._log("Transacao rejeitada (duplicada ou invalida).")

    def _show_pending(self) -> None:
        if not self.node:
            self._log("Inicie o no primeiro.")
            return
        pending = self.node.blockchain.pending_transactions
        if not pending:
            self._log("Nenhuma transacao pendente.")
            return
        self._log("Transacoes pendentes:")
        for tx in pending:
            self._log(f"- {tx.id[:8]} {tx.origem} -> {tx.destino}: {tx.valor}")

    def _mine_block(self) -> None:
        if not self.node:
            self._log("Inicie o no primeiro.")
            return

        def run_mine() -> None:
            # Mineracao em thread separada para nao travar a GUI.
            self._log("Mineracao iniciada...")
            start = time.time()
            block = self.node.mine()
            elapsed = time.time() - start
            if block:
                self._log(
                    f"Bloco #{block.index} minerado em {elapsed:.2f}s | hash {block.hash}"
                )
            else:
                self._log("Mineracao interrompida.")

        threading.Thread(target=run_mine, daemon=True).start()

    def _show_blockchain(self) -> None:
        if not self.node:
            self._log("Inicie o no primeiro.")
            return
        self._log("Blockchain:")
        for block in self.node.blockchain.chain:
            self._log(
                f"Bloco #{block.index} | hash {block.hash[:16]}... | txs {len(block.transactions)}"
            )

    def _show_balance(self) -> None:
        if not self.node:
            self._log("Inicie o no primeiro.")
            return
        address = self.balance_addr_var.get().strip()
        if not address:
            self._log("Informe um endereco.")
            return
        if not is_host_port_address(address):
            self._log("Endereco invalido. Use o formato host:porta.")
            return
        # Saldo calculado localmente a partir da blockchain replicada.
        balance = self.node.blockchain.get_balance(address)
        self._log(f"Saldo de {address}: {balance}")

    def _show_peers(self) -> None:
        if not self.node:
            self._log("Inicie o no primeiro.")
            return
        if not self.node.peers:
            self._log("Nenhum peer conectado.")
            return
        self._log("Peers:")
        for peer in sorted(self.node.peers):
            self._log(f"- {peer}")

    def _connect_peer(self) -> None:
        if not self.node:
            self._log("Inicie o no primeiro.")
            return
        peer = self.peer_var.get().strip()
        if not peer:
            self._log("Informe o endereco do peer.")
            return
        if not is_host_port_address(peer):
            self._log("Endereco invalido. Use o formato host:porta.")
            return
        # Conexao manual a um peer especifico.
        if self.node.connect_to_peer(peer):
            self._log(f"Conectado ao peer {peer}")
        else:
            self._log("Falha ao conectar ao peer.")

    def _sync_chain(self) -> None:
        if not self.node:
            self._log("Inicie o no primeiro.")
            return
        # Solicita a cadeia aos peers e substitui se houver uma maior.
        self._log("Sincronizando blockchain...")
        self.node.sync_blockchain()
        self._log(f"Blockchain com {len(self.node.blockchain.chain)} blocos")

    def _on_close(self) -> None:
        if self.node:
            self.node.stop()
        self.root.destroy()


def run() -> None:
    root = tk.Tk()
    app = BlockchainApp(root)
    root.mainloop()


if __name__ == "__main__":
    run()
