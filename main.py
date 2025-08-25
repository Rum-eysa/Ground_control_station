# main.py - Ana uygulama başlatıcı
import sys
import logging
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from gui.main_window import MainWindow
from core.logger import setup_logging
from core.config_manager import ConfigManager
import os
import sys

os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(
    os.path.dirname(sys.modules["PyQt5"].__file__), "Qt5", "plugins", "platforms")


def main():
    # Logging sistemi başlat
    setup_logging()
    
    app = QApplication(sys.argv)
    
    # Splash screen
    pixmap = QPixmap("resources/logo.png")
    splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    splash.show()

    app.processEvents()
    
    # Ana pencereyi başlat
    main_window = MainWindow()
    main_window.show()
    
    splash.finish(main_window)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()