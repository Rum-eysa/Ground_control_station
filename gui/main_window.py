# gui/main_window.py - Ana PyQt5 penceresi
# =============================================================================

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from .camera_widget import CameraWidget
from .control_panel import ControlPanel
from .side_menu import SideMenu
from .status_bar import CustomStatusBar
from .connection_dialog import ConnectionDialog
from .quick_connect import QuickConnect
from .styles import MAIN_STYLE

from core.device_manager import DeviceManager
from core.config_manager import ConfigManager
from core.logger import setup_logging
from core.video_recorder import VideoRecorder

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ground Control Station v2.0")
        self.setGeometry(100, 100, 1400, 900)
        self.setStyleSheet(MAIN_STYLE)
        
        # Core bileşenleri oluştur
        self.config_manager = ConfigManager()
        self.logger = setup_logging()
        
        # DeviceManager'ı doğru şekilde başlat (config_manager ve logger ile)
        self.device_manager = DeviceManager(self.config_manager, self.logger)
        self.video_recorder = VideoRecorder()
        
        # UI bileşenler
        self.camera_widget = None
        self.control_panel = None
        self.side_menu = None
        self.quick_connect = None
        
        # UI'yi başlat
        self.init_ui()
        self.setup_connections()
        self.setup_shortcuts()
        
        # Otomatik cihaz keşfi başlat
        self.device_manager.start_discovery()
    
    def init_ui(self):
        """UI bileşenlerini başlat"""
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Ana layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Sol menü
        self.side_menu = SideMenu()
        self.side_menu.setMaximumWidth(250)
        main_layout.addWidget(self.side_menu)
        
        # Orta bölüm (kamera + kontroller)
        center_layout = QVBoxLayout()
        
        # Hızlı bağlantı paneli
        self.quick_connect = QuickConnect()
        center_layout.addWidget(self.quick_connect)
        
        # Kamera widget'ı
        self.camera_widget = CameraWidget()
        center_layout.addWidget(self.camera_widget, 1)  # Stretch factor 1
        
        main_layout.addLayout(center_layout, 1)  # Ana alan
        
        # Sağ kontrol paneli
        self.control_panel = ControlPanel()
        self.control_panel.setMaximumWidth(300)
        main_layout.addWidget(self.control_panel)
        
        # Durum çubuğu
        self.status_bar = CustomStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Menü çubuğu
        self.create_menu_bar()
        
        # Toolbar
        self.create_toolbar()
    
    def create_menu_bar(self):
        """Menü çubuğunu oluştur"""
        menubar = self.menuBar()
        
        # Dosya menüsü
        file_menu = menubar.addMenu('Dosya')
        
        # Kayıt başlat/durdur
        record_action = QAction('Kayıt Başlat', self)
        record_action.setShortcut('Ctrl+R')
        record_action.triggered.connect(self.toggle_recording)
        file_menu.addAction(record_action)
        
        file_menu.addSeparator()
        
        # Çıkış
        exit_action = QAction('Çıkış', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Bağlantı menüsü
        connection_menu = menubar.addMenu('Bağlantı')
        
        # Cihaz keşfi
        discover_action = QAction('Cihaz Keşfi', self)
        discover_action.setShortcut('Ctrl+D')
        discover_action.triggered.connect(self.start_discovery)
        connection_menu.addAction(discover_action)
        
        # Hızlı bağlantı
        quick_connect_action = QAction('Hızlı Bağlantı', self)
        quick_connect_action.setShortcut('Ctrl+Shift+C')
        quick_connect_action.triggered.connect(self.show_quick_connect)
        connection_menu.addAction(quick_connect_action)
        
        connection_menu.addSeparator()
        
        # Raspberry Pi bağlantı
        raspberry_action = QAction('Raspberry Pi Bağlan', self)
        raspberry_action.triggered.connect(self.connect_raspberry)
        connection_menu.addAction(raspberry_action)
        
        # Jetson bağlantı
        jetson_action = QAction('Jetson Bağlan', self)
        jetson_action.triggered.connect(self.connect_jetson)
        connection_menu.addAction(jetson_action)
        
        # Yardım menüsü
        help_menu = menubar.addMenu('Yardım')
        
        about_action = QAction('Hakkında', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Toolbar oluştur"""
        toolbar = self.addToolBar('Ana Toolbar')
        toolbar.setMovable(False)
        
        # Cihaz keşfi butonu
        discover_btn = QAction('🔍 Cihaz Ara', self)
        discover_btn.triggered.connect(self.start_discovery)
        toolbar.addAction(discover_btn)
        
        toolbar.addSeparator()
        
        # Raspberry Pi bağlantı butonu
        raspberry_btn = QAction('📱 Raspberry', self)
        raspberry_btn.triggered.connect(self.connect_raspberry)
        toolbar.addAction(raspberry_btn)
        
        # Jetson bağlantı butonu
        jetson_btn = QAction('🖥️ Jetson', self)
        jetson_btn.triggered.connect(self.connect_jetson)
        toolbar.addAction(jetson_btn)
        
        toolbar.addSeparator()
        
        # Kayıt butonu
        self.record_btn = QAction('⏺️ Kayıt', self)
        self.record_btn.triggered.connect(self.toggle_recording)
        toolbar.addAction(self.record_btn)
        
        # Screenshot butonu
        screenshot_btn = QAction('📷 Ekran Görüntüsü', self)
        screenshot_btn.triggered.connect(self.take_screenshot)
        toolbar.addAction(screenshot_btn)
    
    def setup_connections(self):
        """Sinyal bağlantılarını kur"""
        # Device Manager sinyalleri
        self.device_manager.device_found.connect(self.on_device_found)
        self.device_manager.device_connected.connect(self.on_device_connected)
        self.device_manager.device_disconnected.connect(self.on_device_disconnected)
        self.device_manager.status_changed.connect(self.status_bar.showMessage)
        
        # Quick Connect sinyalleri
        self.quick_connect.connect_requested.connect(self.on_manual_connect)
        
        # Control Panel sinyalleri
        self.control_panel.recording_requested.connect(self.toggle_recording)
        self.control_panel.screenshot_requested.connect(self.take_screenshot)
        
        # Side Menu sinyalleri
        self.side_menu.action_requested.connect(self.handle_menu_action)
    
    def setup_shortcuts(self):
        """Klavye kısayollarını ayarla"""
        # Global kısayollar
        QShortcut(QKeySequence("Ctrl+1"), self, self.connect_raspberry)
        QShortcut(QKeySequence("Ctrl+2"), self, self.connect_jetson)
        QShortcut(QKeySequence("Space"), self, self.take_screenshot)
        QShortcut(QKeySequence("Ctrl+Shift+R"), self, self.quick_recovery)
        QShortcut(QKeySequence("F5"), self, self.start_discovery)
    
    def on_device_found(self, device_info):
        """Cihaz bulunduğunda çağrılır"""
        self.side_menu.add_device(device_info)
        self.quick_connect.add_device(device_info)
        
        device_type = device_info.get('type', 'unknown')
        ip = device_info.get('ip', 'unknown')
        
        self.status_bar.showMessage(f"{device_type.title()} cihazı bulundu: {ip}", 5000)
    
    def on_device_connected(self, device_type, ip):
        """Cihaz bağlandığında çağrılır"""
        self.status_bar.set_connection_status(device_type, True)
        
        # Kamera akışını bağla
        if ip in self.device_manager.camera_clients:
            camera_client = self.device_manager.camera_clients[ip]
            camera_client.frame_received.connect(self.camera_widget.update_frame)
            camera_client.connection_status.connect(
                lambda status: self.status_bar.set_video_status(status)
            )
        
        QMessageBox.information(
            self, 
            "Bağlantı Başarılı", 
            f"{device_type.title()} cihazına bağlantı kuruldu: {ip}"
        )
    
    def on_device_disconnected(self, device_type, ip):
        """Cihaz bağlantısı kesildiğinde çağrılır"""
        self.status_bar.set_connection_status(device_type, False)
        self.status_bar.set_video_status(False)
        
        QMessageBox.warning(
            self, 
            "Bağlantı Kesildi", 
            f"{device_type.title()} cihazının bağlantısı kesildi: {ip}"
        )
    
    def on_manual_connect(self, ip, device_type):
        """Manuel bağlantı isteği"""
        if device_type == 'raspberry':
            self.device_manager.connect_raspberry(ip)
        elif device_type == 'jetson':
            self.device_manager.connect_jetson(ip)
    
    def start_discovery(self):
        """Cihaz keşfi başlat"""
        self.device_manager.start_discovery()
        self.status_bar.showMessage("Cihaz keşfi başlatıldı...", 3000)
    
    def connect_raspberry(self):
        """Raspberry Pi'ye bağlan"""
        self.device_manager.connect_raspberry()
    
    def connect_jetson(self):
        """Jetson'a bağlan"""
        self.device_manager.connect_jetson()
    
    def quick_recovery(self):
        """Hızlı bağlantı kurtarma"""
        recovered = self.device_manager.quick_recovery()
        self.status_bar.showMessage(f"Kurtarma tamamlandı: {recovered} cihaz", 5000)
    
    def toggle_recording(self):
        """Video kaydını başlat/durdur"""
        if self.video_recorder.is_recording:
            self.video_recorder.stop_recording()
            self.record_btn.setText('⏺️ Kayıt')
            self.status_bar.showMessage("Kayıt durduruldu", 3000)
        else:
            # Aktif kamera frame'ini kayda başla
            current_frame = self.camera_widget.get_current_frame()
            if current_frame is not None:
                self.video_recorder.start_recording(current_frame.shape)
                self.record_btn.setText('⏹️ Durdur')
                self.status_bar.showMessage("Kayıt başlatıldı", 3000)
                
                # Frame'leri kaydetmek için bağlantı kur
                self.camera_widget.frame_updated.connect(
                    self.video_recorder.add_frame
                )
    
    def take_screenshot(self):
        """Ekran görüntüsü al"""
        frame = self.camera_widget.get_current_frame()
        if frame is not None:
            from core.screenshot_manager import ScreenshotManager
            screenshot_manager = ScreenshotManager()
            filename = screenshot_manager.save_screenshot(frame)
            self.status_bar.showMessage(f"Ekran görüntüsü kaydedildi: {filename}", 5000)
    
    def show_quick_connect(self):
        """Hızlı bağlantı dialog'unu göster"""
        dialog = ConnectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            connection_info = dialog.get_connection_info()
            device_type = connection_info.get('type')
            ip = connection_info.get('ip')
            
            self.on_manual_connect(ip, device_type)
    
    def handle_menu_action(self, action):
        """Side menu aksiyonlarını işle"""
        if action == 'settings':
            self.show_settings()
        elif action == 'logs':
            self.show_logs()
        elif action == 'about':
            self.show_about()
    
    def show_settings(self):
        """Ayarlar penceresini göster"""
        # TODO: Ayarlar dialog'u implement edilecek
        QMessageBox.information(self, "Ayarlar", "Ayarlar penceresi yakında eklenecek!")
    
    def show_logs(self):
        """Log penceresini göster"""
        # TODO: Log görüntüleyici implement edilecek
        QMessageBox.information(self, "Loglar", "Log görüntüleyici yakında eklenecek!")
    
    def show_about(self):
        """Hakkında penceresini göster"""
        QMessageBox.about(
            self, 
            "Hakkında", 
            "Ground Control Station v2.0\n\n"
            "Gelişmiş drone kontrol ve video akış sistemi\n"
            "Raspberry Pi ve Jetson desteği ile\n\n"
            "Geliştirici: Takım Adı\n"
            "2025"
        )
    
    def closeEvent(self, event):
        """Pencere kapatılırken çağrılır"""
        # Tüm bağlantıları kapat
        for ip in list(self.device_manager.camera_clients.keys()):
            self.device_manager.disconnect_device(ip)
        
        # Kayıt varsa durdur
        if self.video_recorder.is_recording:
            self.video_recorder.stop_recording()
        
        event.accept()