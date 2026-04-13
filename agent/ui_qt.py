"""PySide6 (Qt) UI for the LM Wiki synthesizer."""

from __future__ import annotations

import html
import logging
import sys
from collections.abc import Callable

from PySide6.QtCore import QEvent, QObject, QSize, Qt, QThread, QTimer
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QMouseEvent,
    QPainter,
    QPalette,
    QPixmap,
    QShowEvent,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from logutil import LOGGER_NAME, setup_logging
from synthesizer import SynthesizerConfig, WikiRepository, WikiSynthesizer
from ui_stylesheet import APPLICATION_STYLESHEET
from window_log import QtLogEmitter, QtPanelLogHandler, WindowLog

_RAW_LIST_BG = QColor("#282c34")
_RAW_LIST_BG_ALT = QColor("#2c313a")
_RAW_LIST_FG = QColor("#abb2bf")
_RAW_LIST_SEL_BG = QColor("#e06c75")
_RAW_LIST_SEL_FG = QColor("#000000")

_RAW_LIST_ICON_PX = 18
_RAW_LIST_BULLET_D = 7
_RAW_LIST_BULLET_NORMAL = QColor("#7f848e")
_RAW_LIST_BULLET_SELECTED = QColor("#1e222a")
_raw_list_bullet_icon_cache: tuple[QIcon, QIcon] | None = None


def _raw_list_label_with_image_count(name: str, image_count: int) -> str:
    if image_count == 1:
        suffix = "[1 image]"
    else:
        suffix = f"[{image_count} images]"
    return f"{name} {suffix}"


def _raw_item_basename(item: QListWidgetItem) -> str:
    data = item.data(Qt.ItemDataRole.UserRole)
    if isinstance(data, str) and data:
        return data
    return item.text()


def _log_color_for_level(levelno: int) -> str:
    """Hex colors aligned with One Dark; stderr stays unstyled."""
    if levelno >= logging.CRITICAL:
        return "#ff7b72"  # bright red
    if levelno >= logging.ERROR:
        return "#e06c75"  # salmon (theme accent)
    if levelno >= logging.WARNING:
        return "#e5c07b"  # yellow
    if levelno >= logging.INFO:
        return "#abb2bf"  # default foreground
    # DEBUG and below
    return "#7f848e"  # muted


def _raw_list_bullet_icons() -> tuple[QIcon, QIcon]:
    global _raw_list_bullet_icon_cache
    if _raw_list_bullet_icon_cache is not None:
        return _raw_list_bullet_icon_cache

    def one(color: QColor) -> QIcon:
        sz = _RAW_LIST_ICON_PX
        d = _RAW_LIST_BULLET_D
        pm = QPixmap(sz, sz)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(color)
        p.setPen(Qt.PenStyle.NoPen)
        x = (sz - d) // 2
        p.drawEllipse(x, x, d, d)
        p.end()
        return QIcon(pm)

    _raw_list_bullet_icon_cache = (
        one(_RAW_LIST_BULLET_NORMAL),
        one(_RAW_LIST_BULLET_SELECTED),
    )
    return _raw_list_bullet_icon_cache


def _apply_ui_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    pal = QPalette()
    bg = QColor("#1e222a")
    surface = QColor("#282c34")
    panel = QColor("#21252b")
    text = QColor("#abb2bf")
    muted = QColor("#7f848e")
    accent_teal = QColor("#56b6c2")
    accent_salmon = QColor("#e06c75")
    pal.setColor(QPalette.ColorRole.Window, bg)
    pal.setColor(QPalette.ColorRole.WindowText, text)
    pal.setColor(QPalette.ColorRole.Base, bg)
    pal.setColor(QPalette.ColorRole.AlternateBase, surface)
    pal.setColor(QPalette.ColorRole.ToolTipBase, panel)
    pal.setColor(QPalette.ColorRole.ToolTipText, text)
    pal.setColor(QPalette.ColorRole.Text, text)
    pal.setColor(QPalette.ColorRole.Button, surface)
    pal.setColor(QPalette.ColorRole.ButtonText, text)
    pal.setColor(QPalette.ColorRole.Link, accent_teal)
    pal.setColor(QPalette.ColorRole.Highlight, accent_salmon)
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#1e222a"))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, muted)
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, muted)
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, muted)
    app.setPalette(pal)
    app.setStyleSheet(APPLICATION_STYLESHEET)


def _content_page(title: str, body: str, *, extra: QWidget | None = None) -> QWidget:
    w = QWidget()
    w.setObjectName("contentShell")
    v = QVBoxLayout(w)
    v.setContentsMargins(14, 12, 14, 12)
    v.setSpacing(6)
    t = QLabel(title)
    t.setObjectName("contentTitle")
    v.addWidget(t)
    m = QLabel(body)
    m.setObjectName("contentMuted")
    m.setWordWrap(True)
    v.addWidget(m)
    if extra is not None:
        v.addWidget(extra)
    v.addStretch()
    return w


class SynthesisThread(QThread):
    """Runs WikiSynthesizer.process_raw_files off the GUI thread."""

    def __init__(
        self,
        synth: WikiSynthesizer,
        raw_basenames: list[str],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._synth = synth
        self._raw_basenames = raw_basenames

    def run(self) -> None:
        self._synth.process_raw_files(
            self._raw_basenames,
            cancel_check=self.isInterruptionRequested,
        )


class RawMarkdownListWidget(QListWidget):
    """Toggle row highlight on click; Qt does not emit itemClicked when selection is NoSelection."""

    def __init__(
        self,
        on_toggle: Callable[[QListWidgetItem], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_toggle = on_toggle
        # No QSS on this widget: any QListWidget stylesheet makes Qt ignore item setBackground.
        self.setObjectName("rawFileList")
        self.setAutoFillBackground(True)
        row_font = QFont()
        row_font.setPixelSize(12)
        self.setFont(row_font)
        lp = self.palette()
        lp.setColor(QPalette.ColorRole.Base, _RAW_LIST_BG)
        lp.setColor(QPalette.ColorRole.Text, _RAW_LIST_FG)
        self.setPalette(lp)
        self.setIconSize(QSize(_RAW_LIST_ICON_PX, _RAW_LIST_ICON_PX))
        self.viewport().installEventFilter(self)

    def _item_row_height(self) -> int:
        fm = self.fontMetrics()
        return fm.lineSpacing() + 10

    def addItem(self, *__args) -> None:  # type: ignore[no-untyped-def]
        super().addItem(*__args)
        it = self.item(self.count() - 1)
        if it is not None:
            normal_icon, _ = _raw_list_bullet_icons()
            it.setIcon(normal_icon)
            it.setSizeHint(QSize(0, self._item_row_height()))

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched == self.viewport() and event.type() == QEvent.Type.MouseButtonPress:
            me = event
            if isinstance(me, QMouseEvent) and me.button() == Qt.MouseButton.LeftButton:
                pos = me.position().toPoint()
                idx = self.indexAt(pos)
                if idx.isValid():
                    it = self.itemFromIndex(idx)
                    if it is not None:
                        self._on_toggle(it)
        return super().eventFilter(watched, event)


class MainWindow(QMainWindow):
    """One Dark–style shell: panel header/sidebar, salmon selection, teal actions."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LM Wiki")
        self.resize(1280, 680)
        self._cfg = SynthesizerConfig()
        self._repo = WikiRepository(self._cfg)
        self._synth = WikiSynthesizer(self._cfg)
        self._raw_file_list: QListWidget | None = None
        self._raw_status: QLabel | None = None
        self._btn_synth_selected: QPushButton | None = None
        self._btn_synth_all: QPushButton | None = None
        self._btn_synth_page: QPushButton | None = None
        self._cancel_btns: list[QPushButton] = []
        self._synth_thread: QThread | None = None
        self._raw_selected: set[str] = set()
        self._main_splitter: QSplitter | None = None
        self._log: QTextEdit | None = None
        self._splitter_sizes_initialized = False

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_header())

        self._main_splitter = QSplitter(Qt.Orientation.Vertical)
        self._main_splitter.setChildrenCollapsible(False)
        self._main_splitter.addWidget(self._build_body())
        self._log = self._build_log_panel()
        self._main_splitter.addWidget(self._log)
        root_layout.addWidget(self._main_splitter, stretch=1)

        self.setCentralWidget(root)
        self._window_log = WindowLog(self.append_log_line)
        self._log_emitter = QtLogEmitter(self._window_log, self)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(30)
        header.setObjectName("topHeader")
        h = QHBoxLayout(header)
        h.setContentsMargins(10, 0, 10, 0)
        h.setSpacing(6)

        wordmark = QLabel("LM Wiki")
        wordmark.setObjectName("headerWordmark")
        h.addWidget(wordmark)
        h.addStretch()
        return header

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if not self._splitter_sizes_initialized and self._main_splitter is not None:
            QTimer.singleShot(0, self._apply_initial_splitter_sizes)

    def _apply_initial_splitter_sizes(self) -> None:
        if self._splitter_sizes_initialized or self._main_splitter is None:
            return
        h = self._main_splitter.height()
        if h <= 0:
            return
        self._main_splitter.setSizes([int(h * 0.8), int(h * 0.2)])
        self._splitter_sizes_initialized = True

    def _build_log_panel(self) -> QTextEdit:
        log = QTextEdit()
        log.setObjectName("appLog")
        log.setReadOnly(True)
        log.setAcceptRichText(True)
        log.setPlaceholderText("Log output…")
        log.setMinimumHeight(80)
        log.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        f = QFont()
        f.setStyleHint(QFont.StyleHint.Monospace)
        f.setPointSize(10)
        log.setFont(f)
        return log

    def append_log_line(self, levelno: int, text: str) -> None:
        if self._log is None:
            return
        color = _log_color_for_level(levelno)
        safe = html.escape(text, quote=True)
        self._log.moveCursor(QTextCursor.MoveOperation.End)
        self._log.insertHtml(
            f'<span style="color:{color}; font-family:monospace; font-size:10pt;">{safe}</span><br>'
        )
        self._log.moveCursor(QTextCursor.MoveOperation.End)
        self._log.ensureCursorVisible()

    def _build_body(self) -> QWidget:
        body = QWidget()
        bl = QHBoxLayout(body)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(0)

        # Stack must exist before sidebar: initial nav setChecked fires toggled -> _on_sidebar_nav
        self._stack = QStackedWidget()
        self._stack.setObjectName("contentShell")

        raw_page = self._build_raw_files_panel()
        synth_row = QWidget()
        synth_h = QHBoxLayout(synth_row)
        synth_h.setContentsMargins(0, 0, 0, 0)
        synth_h.setSpacing(8)
        synth_extra = QPushButton("Synthesize All")
        synth_extra.setObjectName("primaryOutline")
        synth_extra.clicked.connect(self._on_synthesize_all)
        self._btn_synth_page = synth_extra
        cancel_page = QPushButton("Cancel synthesis")
        cancel_page.setObjectName("synthCancel")
        cancel_page.setVisible(False)
        cancel_page.clicked.connect(self._on_cancel_synthesis)
        self._cancel_btns.append(cancel_page)
        synth_h.addWidget(synth_extra)
        synth_h.addWidget(cancel_page)
        synth_h.addStretch()
        synth = _content_page(
            "Synthesize",
            "Batch synthesis sends each raw note to Gemini and writes concept files.",
            extra=synth_row,
        )

        self._stack.addWidget(raw_page)
        self._stack.addWidget(synth)

        sidebar = self._build_sidebar()
        bl.addWidget(sidebar)
        bl.addWidget(self._stack, stretch=1)
        return body

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(198)
        sidebar.setObjectName("sidebar")
        v = QVBoxLayout(sidebar)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(2)

        title = QLabel("LM Wiki")
        title.setObjectName("sidebarTitle")
        v.addWidget(title)

        v.addSpacing(6)

        nav_specs = [
            ("Raw files", 0, self._refresh_raw_files_list),
            ("Synthesize all", 1, None),
        ]
        group = QButtonGroup(self)
        group.setExclusive(True)
        for label, page_idx, hook in nav_specs:

            def make_handler(p: int, h):
                def on_toggled(checked: bool) -> None:
                    if checked:
                        self._on_sidebar_nav(p, h)

                return on_toggled

            btn = QPushButton(label)
            btn.setObjectName("sidebarNav")
            btn.setCheckable(True)
            btn.toggled.connect(make_handler(page_idx, hook))
            group.addButton(btn)
            v.addWidget(btn)

        group.buttons()[0].setChecked(True)

        v.addStretch()

        exit_btn = QPushButton("Exit system")
        exit_btn.setObjectName("sidebarExit")
        exit_btn.clicked.connect(self._on_exit)
        v.addWidget(exit_btn)

        foot = QLabel("LAST SYNC —")
        foot.setObjectName("sidebarFooter")
        v.addWidget(foot)

        return sidebar

    def _on_sidebar_nav(self, page_index: int, hook) -> None:
        self._stack.setCurrentIndex(page_index)
        if hook is not None:
            hook()

    def _build_raw_files_panel(self) -> QWidget:
        w = QWidget()
        w.setObjectName("contentShell")
        v = QVBoxLayout(w)
        # Match sidebar column: 8px inset, 2px between stacked rows (see _build_sidebar).
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(2)
        title = QLabel("Raw files")
        title.setObjectName("sidebarTitle")
        v.addWidget(title)
        v.addSpacing(6)
        self._raw_status = QLabel()
        self._raw_status.setObjectName("contentMuted")
        self._raw_status.setWordWrap(True)
        v.addWidget(self._raw_status)
        self._raw_file_list = RawMarkdownListWidget(self._toggle_raw_item)
        self._raw_file_list.setAlternatingRowColors(False)
        self._raw_file_list.setUniformItemSizes(True)
        self._raw_file_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._raw_file_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        list_frame = QFrame()
        list_frame.setObjectName("rawListFrame")
        fl = QVBoxLayout(list_frame)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(0)
        fl.addWidget(self._raw_file_list)
        v.addWidget(list_frame, stretch=1)

        v.addSpacing(6)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self._btn_synth_selected = QPushButton("Synthesize 0 Selected")
        self._btn_synth_selected.setObjectName("rawSynthSelected")
        self._btn_synth_selected.setEnabled(False)
        self._btn_synth_selected.clicked.connect(self._on_synthesize_selected)
        self._btn_synth_all = QPushButton("Synthesize All")
        self._btn_synth_all.setObjectName("rawSynthAll")
        self._btn_synth_all.clicked.connect(self._on_synthesize_all)
        cancel_raw = QPushButton("Cancel synthesis")
        cancel_raw.setObjectName("synthCancel")
        cancel_raw.setVisible(False)
        cancel_raw.clicked.connect(self._on_cancel_synthesis)
        self._cancel_btns.append(cancel_raw)
        btn_row.addWidget(self._btn_synth_selected)
        btn_row.addWidget(self._btn_synth_all)
        btn_row.addWidget(cancel_raw)
        btn_row.addStretch()
        v.addLayout(btn_row)

        return w

    def _refresh_raw_files_list(self) -> None:
        """Load basenames from raw/ via WikiRepository.list_raw_source_files."""
        if self._raw_file_list is None or self._raw_status is None:
            return
        raw_dir = self._repo.raw_dir
        if not raw_dir.is_dir():
            self._raw_selected.clear()
            self._raw_file_list.clear()
            self._raw_status.setText(f"Raw directory not found: {raw_dir}")
            self._update_synth_selected_button_state()
            return
        names = self._repo.list_raw_source_files()
        self._raw_selected.clear()
        self._raw_file_list.clear()
        for name in names:
            n_img = len(self._repo.list_companion_image_basenames(name))
            label = _raw_list_label_with_image_count(name, n_img)
            it = QListWidgetItem(label)
            it.setData(Qt.ItemDataRole.UserRole, name)
            self._raw_file_list.addItem(it)
        self._apply_raw_list_row_colors()
        if not names:
            self._raw_status.setText(
                f"No .md or .txt files in {raw_dir} (top-level only, excludes subfolders)."
            )
        else:
            self._raw_status.setText(f"{len(names)} raw file(s) (.md/.txt) in {raw_dir}.")
        self._update_synth_selected_button_state()

    def _update_synth_selected_button_state(self) -> None:
        if self._btn_synth_selected is not None:
            n = len(self._raw_selected)
            self._btn_synth_selected.setText(f"Synthesize {n} Selected")
            self._btn_synth_selected.setEnabled(n > 0)

    def _toggle_raw_item(self, item: QListWidgetItem) -> None:
        name = _raw_item_basename(item)
        if name in self._raw_selected:
            self._raw_selected.discard(name)
        else:
            self._raw_selected.add(name)
        self._apply_raw_list_row_colors()
        self._update_synth_selected_button_state()

    def _apply_raw_list_row_colors(self) -> None:
        if self._raw_file_list is None:
            return
        normal_icon, sel_icon = _raw_list_bullet_icons()
        for i in range(self._raw_file_list.count()):
            it = self._raw_file_list.item(i)
            if it is None:
                continue
            n = _raw_item_basename(it)
            if n in self._raw_selected:
                it.setBackground(QBrush(_RAW_LIST_SEL_BG))
                it.setForeground(QBrush(_RAW_LIST_SEL_FG))
                it.setIcon(sel_icon)
            else:
                stripe = _RAW_LIST_BG if i % 2 == 0 else _RAW_LIST_BG_ALT
                it.setBackground(QBrush(stripe))
                it.setForeground(QBrush(_RAW_LIST_FG))
                it.setIcon(normal_icon)

    def _set_synthesis_ui_busy(self, busy: bool) -> None:
        for b in (
            self._btn_synth_selected,
            self._btn_synth_all,
            self._btn_synth_page,
        ):
            if b is not None:
                b.setEnabled(not busy)
        for cb in self._cancel_btns:
            cb.setVisible(busy)
            cb.setEnabled(busy)

    def _start_synthesis_thread(self, names: list[str], label: str) -> None:
        if self._synth_thread is not None and self._synth_thread.isRunning():
            self._window_log.warning("Synthesis already running; wait for it to finish.")
            return
        if not names:
            return
        self._window_log.info(f"{label} ({len(names)} file(s)): {', '.join(names)}")
        self._set_synthesis_ui_busy(True)
        worker = SynthesisThread(self._synth, names, self)
        self._synth_thread = worker
        worker.finished.connect(self._on_synthesis_thread_finished)
        worker.start()

    def _on_synthesis_thread_finished(self) -> None:
        t = self._synth_thread
        was_cancelled = bool(t is not None and t.isInterruptionRequested())
        self._set_synthesis_ui_busy(False)
        self._synth_thread = None
        if t is not None:
            t.deleteLater()
        if was_cancelled:
            self._window_log.warning("Synthesis cancelled.")
        self._refresh_raw_files_list()

    def _on_synthesize_selected(self) -> None:
        if not self._raw_selected:
            return
        names = sorted(self._raw_selected)
        self._start_synthesis_thread(names, "Synthesize selected")

    def _on_cancel_synthesis(self) -> None:
        t = self._synth_thread
        if t is None or not t.isRunning():
            return
        t.requestInterruption()
        for cb in self._cancel_btns:
            cb.setEnabled(False)
        self._window_log.warning(
            "Cancel requested; will stop after the current file (API call cannot be aborted)."
        )

    def _on_synthesize_all(self) -> None:
        raw_dir = self._repo.raw_dir
        if not raw_dir.is_dir():
            self._window_log.warning(
                f"Synthesize all: raw directory not found: {raw_dir}"
            )
            return
        names = self._repo.list_raw_source_files()
        if not names:
            self._window_log.info(
                "Synthesize all: no .md or .txt files in raw directory "
                f"({raw_dir}, top-level only)."
            )
            return
        self._start_synthesis_thread(names, "Synthesize all")

    @staticmethod
    def _on_exit() -> None:
        QApplication.quit()


def _attach_qt_panel_log_handler(window: MainWindow) -> None:
    lg = logging.getLogger(LOGGER_NAME)
    if any(isinstance(h, QtPanelLogHandler) for h in lg.handlers):
        return
    h = QtPanelLogHandler(window._log_emitter)
    h.setLevel(lg.level)
    lg.addHandler(h)


def run_app() -> None:
    app = QApplication(sys.argv)
    _apply_ui_theme(app)
    setup_logging()
    window = MainWindow()
    _attach_qt_panel_log_handler(window)
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    run_app()
