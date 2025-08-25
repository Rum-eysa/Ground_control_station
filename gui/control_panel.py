# Control Panel
# gui/control_panel.py - Kontrol paneli widget'ı
# =============================================================================

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class ControlPanel(QWidget):
    recording_requested = pyqtSignal()
    screenshot_requested = pyqtSignal()
    settings_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.init_ui()
        
    def init_ui(self):
        """UI bileşenlerini başlat"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Başlık
        title = QLabel("Kontrol Paneli")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
            padding: 10px;
            background-color: #3e3e3e;
            border-radius: 5px;
        """)
        layout.addWidget(title)
        
        # Kayıt kontrolü
        self.setup_recording_controls(layout)
        
        # Kamera ayarları
        self.setup_camera_settings(layout)
        
        # Bağlantı kontrolü
        self.setup_connection_controls(layout)
        
        # Sistem bilgileri
        self.setup_system_info(layout)
        
        # Stretch ekle
        layout.addStretch()
    
    def setup_recording_controls(self, parent_layout):
        """Kayıt kontrol bileşenleri"""
        group = QGroupBox("Kayıt Kontrolü")
        layout = QVBoxLayout(group)
        
        # Kayıt butonu
        self.record_btn = QPushButton("🔴 Kayıt Başlat")
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        self.record_btn.clicked.connect(self.on_record_clicked)
        layout.addWidget(self.record_btn)
        
        # Screenshot butonu
        screenshot_btn = QPushButton("📷 Ekran Görüntüsü")
        screenshot_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2196f3;
            }
        """)
        screenshot_btn.clicked.connect(self.screenshot_requested.emit)
        layout.addWidget(screenshot_btn)
        
        # Kayıt ayarları
        settings_layout = QFormLayout()
        
        # Kayıt kalitesi
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Düşük", "Orta", "Yüksek", "Ultra"])
        self.quality_combo.setCurrentText("Yüksek")
        settings_layout.addRow("Kalite:", self.quality_combo)
        
        # FPS ayarı
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(30)
        settings_layout.addRow("FPS:", self.fps_spin)
        
        layout.addLayout(settings_layout)
        
        parent_layout.addWidget(group)
    
    def setup_camera_settings(self, parent_layout):
        """Kamera ayar bileşenleri"""
        group = QGroupBox("Kamera Ayarları")
        layout = QVBoxLayout(group)
        
        # Parlaklık
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(QLabel("Parlaklık:"))
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(50)
        self.brightness_value = QLabel("50")
        brightness_layout.addWidget(self.brightness_slider)
        brightness_layout.addWidget(self.brightness_value)
        layout.addLayout(brightness_layout)
        
        # Kontrast
        contrast_layout = QHBoxLayout()
        contrast_layout.addWidget(QLabel("Kontrast:"))
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(0, 100)
        self.contrast_slider.setValue(50)
        self.contrast_value = QLabel("50")
        contrast_layout.addWidget(self.contrast_slider)
        contrast_layout.addWidget(self.contrast_value)
        layout.addLayout(contrast_layout)
        
        # Zoom
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(100, 500)
        self.zoom_slider.setValue(100)
        self.zoom_value = QLabel("1.0x")
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(self.zoom_value)
        layout.addLayout(zoom_layout)
        
        # Slider değişim sinyalleri
        self.brightness_slider.valueChanged.connect(
            lambda v: self.brightness_value.setText(str(v))
        )
        self.contrast_slider.valueChanged.connect(
            lambda v: self.contrast_value.setText(str(v))
        )
        self.zoom_slider.valueChanged.connect(
            lambda v: self.zoom_value.setText(f"{v/100:.1f}x")
        )
        
        parent_layout.addWidget(group)
    
    def setup_connection_controls(self, parent_layout):
        """Bağlantı kontrol bileşenleri"""
        group = QGroupBox("Bağlantı Durumu")
        layout = QVBoxLayout(group)
        
        # Durum LED'leri
        status_layout = QFormLayout()
        
        self.raspberry_status = QLabel("🔴 Bağlı Değil")
        status_layout.addRow("Raspberry Pi:", self.raspberry_status)
        
        self.jetson_status = QLabel("🔴 Bağlı Değil")
        status_layout.addRow("Jetson:", self.jetson_status)
        
        self.video_status = QLabel("🔴 Akış Yok")
        status_layout.addRow("Video Akışı:", self.video_status)
        
        layout.addLayout(status_layout)
        
        # Hızlı bağlantı butonları
        btn_layout = QHBoxLayout()
        
        raspberry_btn = QPushButton("Pi")
        raspberry_btn.setStyleSheet("QPushButton { background-color: #4caf50; }")
        raspberry_btn.clicked.connect(self.connect_raspberry)
        
        jetson_btn = QPushButton("Jetson")
        jetson_btn.setStyleSheet("QPushButton { background-color: #ff9800; }")
        jetson_btn.clicked.connect(self.connect_jetson)
        
        btn_layout.addWidget(raspberry_btn)
        btn_layout.addWidget(jetson_btn)
        layout.addLayout(btn_layout)
        
        parent_layout.addWidget(group)
    
    def setup_system_info(self, parent_layout):
        """Sistem bilgi bileşenleri"""
        group = QGroupBox("Sistem Bilgileri")
        layout = QVBoxLayout(group)
        
        # Bilgi labels
        self.cpu_label = QLabel("CPU: --")
        self.memory_label = QLabel("RAM: --")
        self.disk_label = QLabel("Disk: --")
        self.network_label = QLabel("Ağ: --")
        
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.memory_label)
        layout.addWidget(self.disk_label)
        layout.addWidget(self.network_label)
        
        # Güncelleme timer'ı
        self.info_timer = QTimer()
        self.info_timer.timeout.connect(self.update_system_info)
        self.info_timer.start(5000)  # 5 saniyede bir güncelle
        
        parent_layout.addWidget(group)
    
    def on_record_clicked(self):
        """Kayıt butonu tıklandığında"""
        self.is_recording = not self.is_recording
        
        if self.is_recording:
            self.record_btn.setText("⏹️ Kayıt Durdur")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #757575;
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
        else:
            self.record_btn.setText("🔴 Kayıt Başlat")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #d32f2f;
                    color: white;
                    border: none;
                    padding: 12px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
        
        self.recording_requested.emit()
    
    def connect_raspberry(self):
        """Raspberry Pi bağlantı isteği"""
        # Ana penceredeki device manager'a sinyal gönder
        self.parent().connect_raspberry()
    
    def connect_jetson(self):
        """Jetson bağlantı isteği"""
        # Ana penceredeki device manager'a sinyal gönder
        self.parent().connect_jetson()
    
    def update_connection_status(self, device_type, connected):
        """Bağlantı durumunu güncelle"""
        status_text = "🟢 Bağlı" if connected else "🔴 Bağlı Değil"
        
        if device_type == 'raspberry':
            self.raspberry_status.setText(status_text)
        elif device_type == 'jetson':
            self.jetson_status.setText(status_text)
    
    def update_video_status(self, streaming):
        """Video akış durumunu güncelle"""
        status_text = "🟢 Aktif" if streaming else "🔴 Akış Yok"
        self.video_status.setText(status_text)
    
    def update_system_info(self):
        """Sistem bilgilerini güncelle"""
        import psutil
        
        # CPU kullanımı
        cpu_percent = psutil.cpu_percent(interval=1)
        self.cpu_label.setText(f"CPU: {cpu_percent}%")
        
        # RAM kullanımı
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        self.memory_label.setText(f"RAM: {memory_percent}%")
        
        # Disk kullanımı
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        self.disk_label.setText(f"Disk: {disk_percent:.1f}%")
        
        # Ağ durumu
        network = psutil.net_io_counters()
        if hasattr(self, 'last_bytes_sent'):
            bytes_sent = network.bytes_sent - self.last_bytes_sent
            bytes_recv = network.bytes_recv - self.last_bytes_recv
            self.network_label.setText(f"Ağ: ↑{bytes_sent//1024}KB ↓{bytes_recv//1024}KB")
        
        self.last_bytes_sent = network.bytes_sent
        self.last_bytes_recv = network.bytes_recv