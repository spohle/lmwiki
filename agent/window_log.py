"""Append plain-text lines to the Qt bottom log panel (and optional stdlib bridge)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from functools import partial

from PySide6.QtCore import QTimer


class WindowLog:
    """Writes human-readable lines to a sink (typically ``MainWindow.append_log``)."""

    def __init__(self, sink: Callable[[str], None]) -> None:
        self._sink = sink

    def write(self, message: str) -> None:
        text = message.rstrip("\r\n")
        if not text:
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for line in text.splitlines():
            if line:
                self._sink(f"[{ts}] {line}")

    def info(self, message: str) -> None:
        self.write(f"[INFO] {message}")

    def warning(self, message: str) -> None:
        self.write(f"[WARNING] {message}")

    def error(self, message: str) -> None:
        self.write(f"[ERROR] {message}")


class QtPanelLogHandler(logging.Handler):
    """Forwards ``wiki_synth`` records to ``WindowLog`` on the GUI thread."""

    def __init__(self, window_log: WindowLog) -> None:
        super().__init__()
        self._window_log = window_log
        self.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
        except Exception:
            self.handleError(record)
            return
        QTimer.singleShot(0, partial(self._window_log.write, msg))
