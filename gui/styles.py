# Styles
# gui/styles.py - PyQt stil tanımları
# =============================================================================

MAIN_STYLE = """
QMainWindow {
    background-color: #2b2b2b;
    color: #ffffff;
}

QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 11px;
}

QGroupBox {
    font-weight: bold;
    border: 2px solid #555555;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
    background-color: #353535;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 8px 0 8px;
    color: #ffffff;
    font-size: 12px;
}

QPushButton {
    background-color: #404040;
    border: 1px solid #555555;
    border-radius: 6px;
    color: #ffffff;
    font-weight: bold;
    padding: 8px 16px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border-color: #777777;
}

QPushButton:pressed {
    background-color: #363636;
    border-color: #999999;
}

QPushButton:disabled {
    background-color: #2a2a2a;
    border-color: #3a3a3a;
    color: #666666;
}

QLineEdit {
    background-color: #404040;
    border: 1px solid #555555;
    border-radius: 4px;
    color: #ffffff;
    padding: 6px;
    selection-background-color: #4a90e2;
}

QLineEdit:focus {
    border-color: #4a90e2;
}

QComboBox {
    background-color: #404040;
    border: 1px solid #555555;
    border-radius: 4px;
    color: #ffffff;
    padding: 6px;
    min-width: 6em;
}

QComboBox:hover {
    border-color: #777777;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: #555555;
    border-left-style: solid;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #404040;
    border: 1px solid #555555;
    selection-background-color: #4a90e2;
    color: #ffffff;
}

QSlider::groove:horizontal {
    border: 1px solid #555555;
    height: 6px;
    background: #404040;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #4a90e2;
    border: 1px solid #357abd;
    width: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #5ba0f2;
}

QSpinBox {
    background-color: #404040;
    border: 1px solid #555555;
    border-radius: 4px;
    color: #ffffff;
    padding: 4px;
}

QSpinBox:focus {
    border-color: #4a90e2;
}

QLabel {
    color: #ffffff;
    background-color: transparent;
}

QTextEdit, QPlainTextEdit {
    background-color: #404040;
    border: 1px solid #555555;
    border-radius: 4px;
    color: #ffffff;
    selection-background-color: #4a90e2;
}

QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #666666;
}

QMenuBar {
    background-color: #353535;
    color: #ffffff;
    border-bottom: 1px solid #555555;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
}

QMenuBar::item:selected {
    background-color: #4a90e2;
    border-radius: 4px;
}

QMenu {
    background-color: #353535;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    background-color: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #4a90e2;
}

QToolBar {
    background-color: #353535;
    border: none;
    spacing: 4px;
    padding: 4px;
}

QToolBar::separator {
    background-color: #555555;
    width: 2px;
    margin: 4px;
}

QStatusBar {
    background-color: #353535;
    color: #ffffff;
    border-top: 1px solid #555555;
}

QFrame {
    background-color: transparent;
}

QTabWidget::pane {
    border: 1px solid #555555;
    background-color: #353535;
}

QTabBar::tab {
    background-color: #404040;
    color: #ffffff;
    padding: 8px 16px;
    margin: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #4a90e2;
}

QTabBar::tab:hover {
    background-color: #4a4a4a;
}
"""