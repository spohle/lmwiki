"""LM Wiki desktop app entry point. Run from the repository root: python lmwiki.py"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_agent_path() -> None:
    agent_dir = Path(__file__).resolve().parent / "agent"
    s = str(agent_dir)
    if s not in sys.path:
        sys.path.insert(0, s)


def main() -> None:
    _ensure_agent_path()
    from ui_qt import run_app

    run_app()


if __name__ == "__main__":
    main()
