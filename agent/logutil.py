"""TTY-aware colored logging for the wiki synthesizer CLI (stdlib only).

Per-call color override (TTY only), either:

    log.info("msg", color=Colors.CYAN)
    log.info("msg", extra={"color": Colors.CYAN})

``color`` must not be used inside ``extra`` together with a conflicting ``color=``
keyword; the keyword wins.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

LOGGER_NAME = "wiki_synth"

# LogRecord key used by ColoredFormatter for per-line color (safe: not a LogRecord builtin).
COLOR_EXTRA_KEY = "color"


class Colors:
    """ANSI foreground SGR codes (use with ``color=`` or ``extra={"color": ...}``)."""

    RESET = "\033[0m"
    DIM = "\033[2m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"


def _color_for_level(levelno: int) -> str:
    if levelno == logging.DEBUG:
        return Colors.DIM
    if levelno < logging.ERROR:
        return Colors.YELLOW  # INFO (default LOGLEVEL), WARNING
    return Colors.RED


class ColoredFormatter(logging.Formatter):
    """Message-only format; colors full line by level or per-record override when use_color is True."""

    def __init__(self, use_color: bool) -> None:
        super().__init__("%(message)s")
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        if not self.use_color:
            return msg
        override = getattr(record, COLOR_EXTRA_KEY, None)
        c = _color_for_level(record.levelno) if override is None else override
        return f"{c}{msg}{Colors.RESET}"


def _level_from_env() -> int:
    raw = os.environ.get("LOGLEVEL", "").strip().upper()
    if not raw:
        return logging.INFO
    return getattr(logging, raw, logging.INFO)


def setup_logging(level: int | None = None) -> None:
    """
    Configure the application logger (stderr, colored on TTY).
    Safe to call more than once; extra handlers are not added.
    """
    root = logging.getLogger(LOGGER_NAME)
    if root.handlers:
        if level is not None:
            root.setLevel(level)
            for h in root.handlers:
                h.setLevel(level)
        return

    lvl = level if level is not None else _level_from_env()
    root.setLevel(lvl)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(lvl)
    use_color = getattr(handler.stream, "isatty", lambda: False)()
    handler.setFormatter(ColoredFormatter(use_color=use_color))
    root.addHandler(handler)
    root.propagate = False


class _ColorLoggerAdapter(logging.LoggerAdapter):
    """Maps ``color=`` on log calls into ``extra["color"]`` for ColoredFormatter."""

    def process(self, msg: Any, kwargs: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        color = kwargs.pop("color", None)
        if color is not None:
            extra = kwargs.get("extra")
            merged: dict[str, Any] = dict(extra) if extra else {}
            merged[COLOR_EXTRA_KEY] = color
            kwargs["extra"] = merged
        return msg, kwargs


def get_logger(name: str) -> _ColorLoggerAdapter:
    """Return a logger that supports ``color=`` on ``debug``/``info``/``warning``/``error``/``critical``."""
    base = logging.getLogger(f"{LOGGER_NAME}.{name}")
    return _ColorLoggerAdapter(base, {})
