# gui/camera_widget.py - Kamera görüntü widget'ı
# =============================================================================

from datetime import time
import cv2
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class CameraWidget(QWidget):
    frame_updated = pyqtSignal(np.ndarray)
    
    def __init__(self):
        super().__init__()
        self.current_frame = None
        self.scaled_frame = None
        self.no_signal_text = "Kamera Bağlantısı Bekleniyor..."
        
        self.setMinimumSize(640, 480)
        self.setStyleSheet("""
            CameraWidget {
                background-color: #2b2b2b;
                border: 2px solid #555;
                border-radius: 8px;
            }
        """)
        
        # FPS ve bilgi gösterimi için
        self.show_info = True
        self.fps_counter = 0
        self.last_fps_time = 0
        self.current_fps = 0
    
    def update_frame(self, frame):
        """Yeni frame geldiğinde çağrılır"""
        self.current_frame = frame.copy()
        
        # FPS hesapla
        current_time = time.time()
        if self.last_fps_time > 0:
            time_diff = current_time - self.last_fps_time
            if time_diff > 0:
                self.current_fps = int(1.0 / time_diff)
        
        self.last_fps_time = current_time