# Side Menu
# gui/side_menu.py - Sol açılır menü
# =============================================================================

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class SideMenu(QWidget):
    action_requested = pyqtSignal(str)
    device_selected = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.devices = {}
        self.init_ui()
        
    def init_ui(self):
        """UI bileşenlerini başlat"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Logo/Başlık
        title = QLabel("Ground Control")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #ffffff;
            padding: 15px;
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 #4a90e2, stop: 1 #357abd);
            border-radius: 8px;
            margin-bottom: 10px;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Cihazlar bölümü
        self.setup_devices_section(layout)
        
        # Hızlı aksiyonlar
        self.setup_actions_section(layout)
        
        # Ayarlar bölümü
        self.setup_settings_section(layout)
        
        # Stretch
        layout.addStretch()
        
        # Footer
        footer = QLabel("v2.0 - 2025")
        footer.setStyleSheet("color: #888; font-size: 10px; text-align: center;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)
    
    def setup_devices_section(self, parent_layout):
        """Cihazlar bölümü"""
        group = QGroupBox("Bulunan Cihazlar")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        self.devices_layout = QVBoxLayout(group)
        
        # Başlangıçta boş mesaj
        self.no_devices_label = QLabel("Cihaz bulunamadı")
        self.no_devices_label.setStyleSheet("color: #888; font-style: italic;")
        self.no_devices_label.setAlignment(Qt.AlignCenter)
        self.devices_layout.addWidget(self.no_devices_label)
        
        parent_layout.addWidget(group)
    
    def setup_actions_section(self, parent_layout):
        """Hızlı aksiyonlar bölümü"""
        group = QGroupBox("Hızlı Aksiyonlar")
        layout = QVBoxLayout(group)
        
        # Cihaz keşfi butonu
        discover_btn = self.create_action_button("🔍 Cihaz Ara", "discover")
        layout.addWidget(discover_btn)
        
        # Hızlı bağlantı butonu
        quick_connect_btn = self.create_action_button("⚡ Hızlı Bağlantı", "quick_connect")
        layout.addWidget(quick_connect_btn)
        
        # Bağlantıları onar butonu
        recovery_btn = self.create_action_button("🔧 Bağlantıları Onar", "recovery")
        layout.addWidget(recovery_btn)
        
        # Tüm bağlantıları kes butonu
        disconnect_btn = self.create_action_button("❌ Tümünü Kes", "disconnect_all")
        layout.addWidget(disconnect_btn)
        
        parent_layout.addWidget(group)
    
    def setup_settings_section(self, parent_layout):
        """Ayarlar bölümü"""
        group = QGroupBox("Sistem")
        layout = QVBoxLayout(group)
        
        # Ayarlar butonu
        settings_btn = self.create_action_button("⚙️ Ayarlar", "settings")
        layout.addWidget(settings_btn)
        
        # Loglar butonu
        logs_btn = self.create_action_button("📋 Loglar", "logs")
        layout.addWidget(logs_btn)
        
        # Hakkında butonu
        about_btn = self.create_action_button("ℹ️ Hakkında", "about")
        layout.addWidget(about_btn)
        
        parent_layout.addWidget(group)
    
    def create_action_button(self, text, action):
        """Aksiyon butonu oluştur"""
        btn = QPushButton(text)
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px;
                border: 1px solid #555;
                border-radius: 5px;
                background-color: #404040;
                color: white;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #777;
            }
            QPushButton:pressed {
                background-color: #363636;
            }
        """)
        btn.clicked.connect(lambda: self.action_requested.emit(action))
        return btn
    
    def add_device(self, device_info):
        """Yeni cihaz ekle"""
        ip = device_info['ip']
        device_type = device_info.get('type', 'unknown')
        
        # İlk cihaz ekleniyor
        if not self.devices:
            self.no_devices_label.hide()
        
        # Cihaz zaten var mı kontrol et
        if ip in self.devices:
            return
        
        # Cihaz widget'ı oluştur
        device_widget = self.create_device_widget(device_info)
        self.devices_layout.addWidget(device_widget)
        
        self.devices[ip] = {
            'info': device_info,
            'widget': device_widget
        }
    
    def create_device_widget(self, device_info):
        """Cihaz widget'ı oluştur"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                border: 1px solid #666;
                border-radius: 5px;
                padding: 5px;
                margin: 2px;
                background-color: #3a3a3a;
            }
            QFrame:hover {
                border-color: #888;
                background-color: #454545;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(3)
        
        # Cihaz tipi ikonu
        device_type = device_info.get('type', 'unknown')
        type_icons = {
            'raspberry': '🍓',
            'jetson': '🖥️',
            'unknown': '❓'
        }
        
        # Başlık
        title_layout = QHBoxLayout()
        icon_label = QLabel(type_icons.get(device_type, '❓'))
        icon_label.setFixedSize(20, 20)
        
        name_label = QLabel(device_type.title())
        name_label.setStyleSheet("font-weight: bold; color: white;")
        
        status_label = QLabel("🔴")
        status_label.setToolTip("Bağlı değil")
        
        title_layout.addWidget(icon_label)
        title_layout.addWidget(name_label)
        title_layout.addStretch()
        title_layout.addWidget(status_label)
        
        layout.addLayout(title_layout)
        
        # IP adresi
        ip_label = QLabel(device_info['ip'])
        ip_label.setStyleSheet("color: #ccc; font-size: 11px;")
        layout.addWidget(ip_label)
        
        # Son görülme zamanı
        import time
        last_seen = time.strftime("%H:%M:%S", time.localtime(device_info.get('last_seen', time.time())))
        time_label = QLabel(f"Son: {last_seen}")
        time_label.setStyleSheet("color: #999; font-size: 9px;")
        layout.addWidget(time_label)
        
        # Click event
        widget.mousePressEvent = lambda event: self.device_selected.emit(device_info)
        
        return widget
    
    def update_device_status(self, ip, connected):
        """Cihaz bağlantı durumunu güncelle"""
        if ip in self.devices:
            device_data = self.devices[ip]
            widget = device_data['widget']
            
            # Status label'ını bul ve güncelle
            for child in widget.findChildren(QLabel):
                if child.text() in ['🔴', '🟢']:
                    child.setText('🟢' if connected else '🔴')
                    child.setToolTip('Bağlı' if connected else 'Bağlı değil')
                    break
    
    def remove_device(self, ip):
        """Cihazı kaldır"""
        if ip in self.devices:
            device_data = self.devices[ip]
            widget = device_data['widget']
            
            self.devices_layout.removeWidget(widget)
            widget.deleteLater()
            
            del self.devices[ip]
            
            # Hiç cihaz kalmadıysa mesajı göster
            if not self.devices:
                self.no_devices_label.show()
    
    def clear_devices(self):
        """Tüm cihazları temizle"""
        for ip in list(self.devices.keys()):
            self.remove_device(ip)