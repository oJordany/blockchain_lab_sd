"""Validacoes simples de entrada."""

from __future__ import annotations


def is_host_port_address(address: str) -> bool:
    address = address.strip()
    if not address:
        return False
    if ":" not in address:
        return False
    host, port_str = address.rsplit(":", 1)
    if not host or not port_str.isdigit():
        return False
    port = int(port_str)
    return 1 <= port <= 65535
