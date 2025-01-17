# main.py
import os
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from mainwindow import MainWindow
from qt_material import apply_stylesheet  # Import qt-material
import warnings

if __name__ == "__main__":

    warnings.filterwarnings("ignore")
    app = QApplication(sys.argv)
    sys.stderr = open(os.devnull, 'w')

    # Apply a Material Design theme.
    apply_stylesheet(app, theme='dark_blue.xml')

    # Increase global font size for better readability
    font = app.font()
    font.setPointSize(14)
    app.setFont(font)

    custom_stylesheet = """
        QLabel, QDoubleSpinBox, QPushButton, QTableWidget {
            font-size: 14pt;
        }
        QPushButton {
            padding: 10px 20px;
        }
        QTableWidget {
            font-size: 12pt;
        }
    """
    app.setStyleSheet(app.styleSheet() + custom_stylesheet)

    window = MainWindow()
    window.showMaximized()  # Maximize the window on startup
    sys.exit(app.exec_())
