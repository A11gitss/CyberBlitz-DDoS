from PyQt5.QtWidgets import QApplication

MODERN_DARK_THEME = """
/* 
 * ===================================================================
 * Modern Dark Theme for CyberBlitz
 * ===================================================================
 */

/* -----[ Global Styles ]----- */
QWidget {
    background-color: #2B2B2B;
    color: #EAEAEA;
    font-family: "Segoe UI", "Arial", sans-serif;
    font-size: 10pt;
    border: none;
}

/* -----[ QGroupBox - For grouping widgets ]----- */
QGroupBox {
    background-color: #313131;
    border: 1px solid #404040;
    border-radius: 5px;
    margin-top: 1ex; /* space for title */
    padding: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #007ACC;
    font-weight: bold;
    font-size: 11pt;
}

/* -----[ Input Fields: QLineEdit, QSpinBox, QComboBox ]----- */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #3C3F41;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px;
    min-height: 20px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #007ACC;
    background-color: #424549;
}

/* -----[ QComboBox Specifics ]----- */
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: #555;
    border-left-style: solid;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
}

QComboBox QAbstractItemView {
    background-color: #3C3F41;
    border: 1px solid #007ACC;
    selection-background-color: #007ACC;
    selection-color: white;
    outline: 0px;
}

/* -----[ QCheckBox & QRadioButton ]----- */
QCheckBox, QRadioButton {
    spacing: 8px;
}

QCheckBox::indicator, QRadioButton::indicator {
    border: 1px solid #888;
    width: 16px;
    height: 16px;
    border-radius: 4px;
    background-color: #3C3F41;
}

QRadioButton::indicator {
    border-radius: 9px; /* circle */
}

QCheckBox::indicator:hover, QRadioButton::indicator:hover {
    border: 1px solid #007ACC;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #007ACC;
    border: 1px solid #007ACC;
}

/* -----[ QPushButton - General and Advanced ]----- */
QPushButton {
    background-color: #4A4A4A;
    border: 1px solid #555;
    padding: 8px 15px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #5A5A5A;
    border-color: #666;
}

QPushButton:pressed {
    background-color: #404040;
}

/* -----[ START/STOP Buttons - Specific Styling ]----- */
QPushButton#startButton {
    background-color: #2ECC71; /* Green */
    color: white;
    font-size: 12pt;
}
QPushButton#startButton:hover {
    background-color: #27ae60;
}
QPushButton#startButton:pressed {
    background-color: #24a058;
}

QPushButton#stopButton {
    background-color: #E74C3C; /* Red */
    color: white;
    font-size: 12pt;
}
QPushButton#stopButton:hover {
    background-color: #c0392b;
}
QPushButton#stopButton:pressed {
    background-color: #b53425;
}

/* -----[ QTabWidget ]----- */
QTabWidget::pane {
    border: 1px solid #404040;
    border-top: none;
    background-color: #2B2B2B;
}

QTabBar::tab {
    background: #313131;
    border: 1px solid #404040;
    border-bottom: none;
    padding: 8px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-weight: bold;
    color: #AAAAAA;
}

QTabBar::tab:selected {
    background: #2B2B2B;
    color: #FFFFFF;
    border-color: #007ACC;
    border-bottom: 1px solid #2B2B2B; /* Hides bottom border of the tab */
}

QTabBar::tab:!selected:hover {
    background: #3c3c3c;
    color: #FFFFFF;
}

/* -----[ QStatusBar ]----- */
QStatusBar {
    background-color: #212121;
    color: #AAAAAA;
    font-size: 9pt;
}

/* -----[ QPlainTextEdit ]----- */
QPlainTextEdit {
    background-color: #1E1E1E;
    color: #ECECEC;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 5px;
}

/* -----[ QProgressBar ]----- */
QProgressBar {
    border: 1px solid #404040;
    border-radius: 4px;
    text-align: center;
    color: #ECECEC;
    background-color: #3C3F41;
}
QProgressBar::chunk {
    background-color: #007ACC;
    border-radius: 3px;
}

/* -----[ QSplitter ]----- */
QSplitter::handle {
    background-color: #404040;
}
QSplitter::handle:horizontal {
    width: 1px;
}
QSplitter::handle:vertical {
    height: 1px;
}
QSplitter::handle:pressed {
    background-color: #007ACC;
}

/* -----[ Scrollbars ]----- */
QScrollBar:vertical {
    border: none;
    background: #2B2B2B;
    width: 12px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #4A4A4A;
    min-height: 20px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover {
    background: #5A5A5A;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    border: none;
    background: #2B2B2B;
    height: 12px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:horizontal {
    background: #4A4A4A;
    min-width: 20px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal:hover {
    background: #5A5A5A;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}

/* -----[ QTableWidget ]----- */
QTableWidget {
    background-color: #313131;
    border: 1px solid #404040;
    gridline-color: #404040;
}
QHeaderView::section {
    background-color: #3C3F41;
    padding: 4px;
    border: 1px solid #404040;
    font-weight: bold;
}
QTableWidget::item {
    padding: 5px;
}
QTableWidget::item:selected {
    background-color: #007ACC;
    color: white;
}
"""

def apply_theme(app: QApplication):
    """Applies the modern dark theme to the application."""
    app.setStyleSheet(MODERN_DARK_THEME)
