"""Qt Style Sheets (QSS) for the LM Wiki desktop UI.

One Dark–style palette: #1e222a / #21252b, salmon #e06c75, teal #56b6c2.
"""

from __future__ import annotations

APPLICATION_STYLESHEET = """
QMainWindow {
    background-color: #1e222a;
}
#topHeader {
    background-color: #21252b;
    border: none;
    border-bottom: 1px solid #3e4451;
}
QLabel#headerWordmark {
    color: #e06c75;
    font-size: 14px;
    font-weight: 700;
}
#sidebar {
    background-color: #21252b;
    border-right: 1px solid #3e4451;
}
QLabel#sidebarTitle {
    color: #abb2bf;
    font-size: 13px;
    font-weight: 700;
}
QPushButton#sidebarNav {
    text-align: left;
    padding: 4px 8px;
    min-height: 0;
    border: none;
    border-radius: 3px;
    background: transparent;
    color: #abb2bf;
    font-size: 12px;
}
QPushButton#sidebarNav:hover {
    background-color: #2c313a;
}
QPushButton#sidebarNav:checked {
    background-color: #e06c75;
    color: #1e222a;
}
QPushButton#sidebarExit {
    text-align: center;
    padding: 4px 8px;
    min-height: 0;
    border: 1px solid #3e4451;
    border-radius: 3px;
    background-color: #2c313c;
    color: #abb2bf;
    font-size: 11px;
}
QPushButton#sidebarExit:hover {
    border-color: #5c6370;
    background-color: #3e4451;
}
QLabel#sidebarFooter {
    color: #7f848e;
    font-size: 8px;
    letter-spacing: 0.05em;
}
#contentShell {
    background-color: #1e222a;
}
QLabel#contentTitle {
    font-size: 17px;
    font-weight: 700;
    color: #dcdfe4;
}
QLabel#contentMuted {
    color: #7f848e;
    font-size: 12px;
}
QPushButton#primaryOutline {
    background: transparent;
    border: 1px solid #56b6c2;
    color: #56b6c2;
    border-radius: 4px;
    padding: 5px 12px;
    font-weight: 600;
    font-size: 11px;
    min-height: 0;
}
QPushButton#primaryOutline:hover {
    background-color: rgba(86, 182, 194, 0.12);
}
QPushButton#primaryOutline:pressed {
    background-color: rgba(86, 182, 194, 0.22);
}
QPushButton#rawSynthSelected {
    text-align: center;
    background: transparent;
    border: 1px solid #56b6c2;
    color: #56b6c2;
    border-radius: 4px;
    padding: 5px 12px;
    font-weight: 600;
    font-size: 11px;
    min-height: 0;
}
QPushButton#rawSynthSelected:hover:enabled {
    background-color: rgba(86, 182, 194, 0.12);
}
QPushButton#rawSynthSelected:pressed:enabled {
    background-color: rgba(86, 182, 194, 0.22);
}
QPushButton#rawSynthSelected:disabled {
    color: #5c6370;
    background-color: #22252a;
    border-color: #2c313c;
}
QPushButton#rawSynthAll {
    background: transparent;
    border: 1px solid #e06c75;
    color: #e06c75;
    border-radius: 4px;
    padding: 5px 12px;
    font-weight: 600;
    font-size: 11px;
    min-height: 0;
}
QPushButton#rawSynthAll:hover {
    background-color: rgba(224, 108, 117, 0.12);
}
QPushButton#rawSynthAll:pressed {
    background-color: rgba(224, 108, 117, 0.22);
}
QToolTip {
    background-color: #21252b;
    color: #abb2bf;
    border: 1px solid #3e4451;
}
#rawListFrame {
    border: 1px solid #3e4451;
    border-radius: 3px;
    background: transparent;
}
QPlainTextEdit#appLog {
    background-color: #282c34;
    color: #abb2bf;
    border: 1px solid #3e4451;
    border-radius: 3px;
    padding: 6px 8px;
    selection-background-color: #e06c75;
    selection-color: #1e222a;
}
"""
