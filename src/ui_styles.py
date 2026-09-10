"""
《新楓之谷：放置遠征隊》UI 樣式與主題模組 (ui_styles.py)
包含現代深色科技主題 (Modern Dark Theme QSS Stylesheet)
"""

QSS_DARK_THEME = """
QWidget {
    background-color: #0f121a;
    color: #e2e8f0;
    font-family: "Microsoft JhengHei UI", "Microsoft JhengHei", "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: 12px;
}

QFrame.card {
    background-color: #171c28;
    border: 1px solid #2a3447;
    border-radius: 6px;
}

QFrame.card-highlight {
    background-color: #1a2233;
    border: 1px solid #f6ad55;
    border-radius: 6px;
}

QPushButton {
    background-color: #242c3d;
    border: 1px solid #364156;
    border-radius: 4px;
    padding: 4px 8px;
    color: #edf2f7;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2f3a50;
    border-color: #4a5568;
}

QPushButton:pressed {
    background-color: #1a2233;
}

QPushButton:disabled {
    background-color: #181d28;
    color: #4a5568;
    border-color: #222a38;
}

QTabWidget::pane {
    border: 1px solid #2a3447;
    background-color: #141824;
    border-radius: 6px;
}

QTabBar::tab {
    background-color: #181f2f;
    color: #a0aec0;
    padding: 6px 12px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
    font-weight: bold;
}

QTabBar::tab:selected {
    background-color: #25334d;
    color: #ffd700;
    border-bottom: 2px solid #ffd700;
}

QProgressBar {
    background-color: #1a202c;
    border: 1px solid #2d3748;
    border-radius: 3px;
    text-align: center;
    font-size: 10px;
    font-weight: bold;
    color: #ffffff;
}

QScrollBar:vertical {
    background-color: #121622;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #2d3748;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4a5568;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QTextEdit {
    background-color: #11141e;
    border: 1px solid #242c3d;
    border-radius: 4px;
    color: #e2e8f0;
    font-size: 12px;
}

QToolTip {
    background-color: #141824;
    color: #ffffff;
    border: 1.5px solid #ecc94b;
    border-radius: 5px;
    padding: 8px;
    font-size: 12px;
    font-family: "Microsoft JhengHei UI", "Microsoft JhengHei", "Segoe UI", sans-serif;
}
"""

