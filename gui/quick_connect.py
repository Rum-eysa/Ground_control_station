# Quick Connect
# gui/quick_connect.py - Hızlı bağlantı widget'ı
# =============================================================================

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from gui.connection_dialog import ConnectionDialog

class QuickConnect(QWidget):
    connect_requested = pyqtSignal(str, str)  # ip, device_type
    
    def __init__(self):
        super().__init__()
        self.devices = {}
        self.init_ui()
        
    def init_ui(self):
        """UI bileşenlerini başlat"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Başlık
        title = QLabel("Hızlı Bağlantı:")
        title.setStyleSheet("font-weight: bold; color: white;")
        layout.addWidget(title)
        
        # Cihaz seçimi dropdown
        self.device_combo = QComboBox()
        self.device_combo.addItem("Cihaz seçin...")
        self.device_combo.setMinimumWidth(200)
        self.device_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #555;
                border-radius: 3px;
                background-color: #404040;
                color: white;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)
        layout.addWidget(self.device_combo)
        
        # Bağlan butonu
        self.connect_btn = QPushButton("🔗 Bağlan")
        self.connect_btn.setEnabled(False)
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #666;
                color: #999;
            }
        """)
        layout.addWidget(self.connect_btn)
        
        # Manuel bağlantı butonu
        manual_btn = QPushButton("⚙️ Manuel")
        manual_btn.clicked.connect(self.show_manual_dialog)
        manual_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        layout.addWidget(manual_btn)
        
        # Yenile butonu
        refresh_btn = QPushButton("🔄")
        refresh_btn.clicked.connect(self.refresh_devices)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        layout.addWidget(refresh_btn)
        
        # Stretch
        layout.addStretch()
        
        # Combo değişim sinyali
        self.device_combo.currentTextChanged.connect(self.on_device_selection_changed)
    
    def add_device(self, device_info):
        """Yeni cihaz ekle"""
        ip = device_info['ip']
        device_type = device_info.get('type', 'unknown')
        
        # Zaten var mı kontrol et
        if ip in self.devices:
            return
        
        self.devices[ip] = device_info
        
        # Combo'ya ekle
        type_icons = {
            'raspberry': '🍓',
            'jetson': '🖥️',
            'unknown': '❓'
        }
        
        icon = type_icons.get(device_type, '❓')
        display_text = f"{icon} {device_type.title()} - {ip}"
        
        self.device_combo.addItem(display_text, ip)
        
        # İlk cihaz eklendiyse otomatik seç
        if len(self.devices) == 1:
            self.device_combo.setCurrentIndex(1)  # 0. index "Cihaz seçin..."
    
    def on_device_selection_changed(self, text):
        """Cihaz seçimi değiştiğinde"""
        if text == "Cihaz seçin...":
            self.connect_btn.setEnabled(False)
        else:
            self.connect_btn.setEnabled(True)
    
    def on_connect_clicked(self):
        """Bağlan butonuna tıklandığında"""
        current_data = self.device_combo.currentData()
        
        if current_data and current_data in self.devices:
            device_info = self.devices[current_data]
            ip = device_info['ip']
            device_type = device_info.get('type', 'unknown')
            
            self.connect_requested.emit(ip, device_type)
    
    def show_manual_dialog(self):
        """Manuel bağlantı dialog'unu göster"""
        dialog = ConnectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            connection_info = dialog.get_connection_info()
            ip = connection_info.get('ip')
            device_type = connection_info.get('type')
            
            self.connect_requested.emit(ip, device_type)
    
    def refresh_devices(self):
        """Cihaz listesini yenile"""
        # Combo'yu temizle (ilk item hariç)
        while self.device_combo.count() > 1:
            self.device_combo.removeItem(1)
        
        # Cihaz listesini temizle
        self.devices.clear()
        
        # Bağlan butonunu devre dışı bırak
        self.connect_btn.setEnabled(False)
        self.device_combo.setCurrentIndex(0)
        
        # Ana pencereye yenileme sinyali gönder
        parent_window = self.window()
        if hasattr(parent_window, 'start_discovery'):
            parent_window.start_discovery()
