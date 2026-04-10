"""PySide6 (Qt) UI for the LM Wiki synthesizer."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    """Main shell; wire synthesis and file listing in later steps."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LM Wiki")
        self.resize(1600, 800)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setSpacing(16)
        layout.addStretch()

        btn_w = 320

        btn_list = QPushButton("1. List Raw Files")
        btn_list.setFixedWidth(btn_w)
        btn_list.clicked.connect(self._stub_list_raw)

        btn_synth = QPushButton("2. Synthesize All Raw Files")
        btn_synth.setFixedWidth(btn_w)
        btn_synth.clicked.connect(self._stub_synthesize_all)

        btn_exit = QPushButton("3. Exit system")
        btn_exit.setFixedWidth(btn_w)
        btn_exit.clicked.connect(self._on_exit)

        for b in (btn_list, btn_synth, btn_exit):
            layout.addWidget(b, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addStretch()
        self.setCentralWidget(central)

    @staticmethod
    def _stub_list_raw() -> None:
        pass

    @staticmethod
    def _stub_synthesize_all() -> None:
        pass

    @staticmethod
    def _on_exit() -> None:
        QApplication.quit()


def run_app() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    run_app()
