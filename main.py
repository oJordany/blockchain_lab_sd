#!/usr/bin/env python3
"""Ponto de entrada do projeto LSD Blockchain."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


def main() -> None:
    if "--cli" in sys.argv:
        sys.argv.remove("--cli")
        # Modo texto explicito: usa o menu CLI para ambientes sem GUI.
        from lsdchain.cli.app import run as run_cli

        run_cli()
        return

    # GUI e o modo padrao; se Tkinter estiver disponivel, abre a interface.
    from lsdchain.gui.app_tk import run as run_gui

    run_gui()


if __name__ == "__main__":
    main()
