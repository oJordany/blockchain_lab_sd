"""Aplicacao CLI para operar o no da blockchain."""

from __future__ import annotations

import argparse
import time

from ..core.transaction import Transaction
from ..core.validation import is_host_port_address
from ..network.node import Node


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="No da blockchain LSD 2025")
    parser.add_argument("--host", default="localhost", help="Host do no")
    parser.add_argument("--port", type=int, default=5000, help="Porta do no")
    parser.add_argument(
        "--bootstrap",
        nargs="*",
        default=[],
        help="Enderecos bootstrap (ex: localhost:5001)",
    )
    return parser.parse_args()


def _print_menu() -> None:
    print("\n" + "=" * 60)
    print("BLOCKCHAIN LSD 2025 - Menu")
    print("=" * 60)
    print("1. Criar transacao")
    print("2. Ver transacoes pendentes")
    print("3. Minerar bloco")
    print("4. Ver blockchain")
    print("5. Ver saldo")
    print("6. Ver peers conectados")
    print("7. Conectar a peer")
    print("8. Sincronizar blockchain")
    print("0. Sair")
    print("=" * 60)


def _create_transaction(node: Node) -> None:
    print("\n--- Nova Transacao ---")
    origem = input("Origem: ").strip()
    destino = input("Destino: ").strip()
    if not is_host_port_address(origem) or not is_host_port_address(destino):
        print("Endereco invalido. Use o formato host:porta.")
        return
    try:
        valor = float(input("Valor: ").strip())
        tx = Transaction(origem=origem, destino=destino, valor=valor)
        if origem not in ("genesis", "coinbase"):
            saldo = node.blockchain.get_balance(origem)
            if saldo < valor:
                print(f"Saldo insuficiente: {saldo} < {valor}")
                return
        if node.broadcast_transaction(tx):
            print(f"Transacao criada: {tx.id[:8]}...")
        else:
            print("Transacao rejeitada (duplicada ou invalida).")
    except ValueError as exc:
        print(f"Erro: {exc}")


def _show_pending(node: Node) -> None:
    print("\n--- Transacoes Pendentes ---")
    if not node.blockchain.pending_transactions:
        print("Nenhuma transacao pendente.")
        return
    for tx in node.blockchain.pending_transactions:
        print(f"[{tx.id[:8]}...] {tx.origem} -> {tx.destino}: {tx.valor}")


def _mine_block(node: Node) -> None:
    count = len(node.blockchain.pending_transactions)
    print(f"\nMinerando bloco com {count} transacao(oes) + coinbase...")
    start = time.time()
    block = node.mine()
    elapsed = time.time() - start
    if block:
        print(f"Bloco #{block.index} minerado em {elapsed:.2f}s")
        print(f"Hash: {block.hash}")
        print(f"Nonce: {block.nonce}")
    else:
        print("Mineracao interrompida.")


def _show_blockchain(node: Node) -> None:
    print("\n--- Blockchain ---")
    for block in node.blockchain.chain:
        print(f"\n[Bloco #{block.index}]")
        print(f"Hash: {block.hash}")
        print(f"Previous: {block.previous_hash}")
        print(f"Nonce: {block.nonce}")
        print(f"Timestamp: {block.timestamp}")
        print(f"Transacoes: {len(block.transactions)}")
        for tx in block.transactions:
            print(f"  - {tx.origem} -> {tx.destino}: {tx.valor}")


def _show_balance(node: Node) -> None:
    address = input("\nEndereco: ").strip()
    if not is_host_port_address(address):
        print("Endereco invalido. Use o formato host:porta.")
        return
    balance = node.blockchain.get_balance(address)
    print(f"Saldo de {address}: {balance}")


def _show_peers(node: Node) -> None:
    print("\n--- Peers ---")
    if not node.peers:
        print("Nenhum peer conectado.")
        return
    for peer in node.peers:
        print(f"- {peer}")


def _connect_peer(node: Node) -> None:
    peer = input("\nEndereco do peer (host:port): ").strip()
    if not is_host_port_address(peer):
        print("Endereco invalido. Use o formato host:porta.")
        return
    if node.connect_to_peer(peer):
        print(f"Conectado a {peer}")
    else:
        print("Falha ao conectar ao peer.")


def _sync_chain(node: Node) -> None:
    print("\nSincronizando blockchain...")
    node.sync_blockchain()
    print(f"Blockchain com {len(node.blockchain.chain)} blocos.")


def run() -> None:
    args = _parse_args()
    node = Node(host=args.host, port=args.port)
    node.start()

    for bootstrap in args.bootstrap:
        if node.connect_to_peer(bootstrap):
            print(f"Conectado ao bootstrap: {bootstrap}")

    if node.peers:
        node.sync_blockchain()

    try:
        while True:
            _print_menu()
            choice = input("Escolha: ").strip()
            if choice == "1":
                _create_transaction(node)
            elif choice == "2":
                _show_pending(node)
            elif choice == "3":
                _mine_block(node)
            elif choice == "4":
                _show_blockchain(node)
            elif choice == "5":
                _show_balance(node)
            elif choice == "6":
                _show_peers(node)
            elif choice == "7":
                _connect_peer(node)
            elif choice == "8":
                _sync_chain(node)
            elif choice == "0":
                print("Encerrando...")
                break
            else:
                print("Opcao invalida.")
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuario")
    finally:
        node.stop()


if __name__ == "__main__":
    run()
