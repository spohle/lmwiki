"""Append plain-text lines to the Qt bottom log panel (and optional stdlib bridge)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime

from PySide6.QtCore import QObject, Signal


class QtLogEmitter(QObject):
    """
    Lives in the GUI thread. (levelno, message) from any thread; Qt queues delivery so
    WindowLog runs on the GUI thread (required for QTextEdit updates).
    """

    entry = Signal(int, str)

    def __init__(self, window_log: "WindowLog", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.entry.connect(window_log.append)


class WindowLog:
    """Writes human-readable lines to a sink (typically ``MainWindow.append_log_line``)."""

    def __init__(self, sink: Callable[[int, str], None]) -> None:
        self._sink = sink

    def append(self, levelno: int, message: str) -> None:
        """Forward handler output; ``message`` is typically ``[LEVELNAME] ...`` from formatting."""
        text = message.rstrip("\r\n")
        if not text:
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for line in text.splitlines():
            if line:
                self._sink(levelno, f"[{ts}] {line}")

    def write(self, message: str, *, level: int = logging.INFO) -> None:
        text = message.rstrip("\r\n")
        if not text:
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for line in text.splitlines():
            if line:
                self._sink(level, f"[{ts}] {line}")

    def info(self, message: str) -> None:
        self.write(f"[INFO] {message}", level=logging.INFO)

    def warning(self, message: str) -> None:
        self.write(f"[WARNING] {message}", level=logging.WARNING)

    def error(self, message: str) -> None:
        self.write(f"[ERROR] {message}", level=logging.ERROR)


class QtPanelLogHandler(logging.Handler):
    """Forwards ``wiki_synth`` records to the panel via ``QtLogEmitter`` (thread-safe)."""

    def __init__(self, emitter: QtLogEmitter) -> None:
        super().__init__()
        self._emitter = emitter
        self.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
        except Exception:
            self.handleError(record)
            return
        self._emitter.entry.emit(record.levelno, msg)
