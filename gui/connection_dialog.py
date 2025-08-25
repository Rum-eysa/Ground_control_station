# Connection Dialog
# gui/connection_dialog.py - Bağlantı kurulum dialog'u
# =============================================================================

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manuel Bağlantı")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        self.connection_info = {}
        self.init_ui()
    
    def init_ui(self):
        """UI bileşenlerini başlat"""
        layout = QVBoxLayout(self)
        
        # Başlık
        title = QLabel("Manuel Cihaz Bağlantısı")
        title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
            background-color: #3e3e3e;
            border-radius: 5px;
            color: white;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Form alanları
        form_layout = QFormLayout()
        
        # Cihaz tipi
        self.device_type = QComboBox()
        self.device_type.addItems(["Raspberry Pi", "Jetson"])
        form_layout.addRow("Cihaz Tipi:", self.device_type)
        
        # IP adresi
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("192.168.1.100")
        form_layout.addRow("IP Adresi:", self.ip_input)
        
        # SSH kullanıcı adı
        self.username_input = QLineEdit()
        self.username_input.setText("pi")
        form_layout.addRow("Kullanıcı Adı:", self.username_input)
        
        # SSH şifresi
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setText("raspberry")
        form_layout.addRow("Şifre:", self.password_input)
        
        # SSH portu
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(22)
        form_layout.addRow("SSH Port:", self.port_input)
        
        layout.addLayout(form_layout)
        
        # Test bağlantısı butonu
        self.test_btn = QPushButton("🔍 Bağlantıyı Test Et")
        self.test_btn.clicked.connect(self.test_connection)
        layout.addWidget(self.test_btn)
        
        # Durum gösterimi
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Dialog butonları
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Cihaz tipi değiştiğinde varsayılan değerleri güncelle
        self.device_type.currentTextChanged.connect(self.update_defaults)
    
    def update_defaults(self, device_type):
        """Cihaz tipine göre varsayılan değerleri güncelle"""
        if device_type == "Raspberry Pi":
            self.username_input.setText("pi")
            self.password_input.setText("raspberry")
        elif device_type == "Jetson":
            self.username_input.setText("nvidia")
            self.password_input.setText("nvidia")
    
    def test_connection(self):
        """Bağlantıyı test et"""
        self.test_btn.setEnabled(False)
        self.test_btn.setText("Test ediliyor...")
        self.status_label.setText("Bağlantı test ediliyor...")
        
        # Test thread'i başlat
        self.test_thread = ConnectionTestThread(
            self.ip_input.text(),
            self.username_input.text(),
            self.password_input.text(),
            self.port_input.value()
        )
        self.test_thread.test_completed.connect(self.on_test_completed)
        self.test_thread.start()
    
    def on_test_completed(self, success, message):
        """Test tamamlandığında çağrılır"""
        self.test_btn.setEnabled(True)
        self.test_btn.setText("🔍 Bağlantıyı Test Et")
        
        if success:
            self.status_label.setText("✅ " + message)
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("❌ " + message)
            self.status_label.setStyleSheet("color: red;")
    
    def get_connection_info(self):
        """Bağlantı bilgilerini döndür"""
        device_type_map = {
            "Raspberry Pi": "raspberry",
            "Jetson": "jetson"
        }
        
        return {
            'type': device_type_map[self.device_type.currentText()],
            'ip': self.ip_input.text(),
            'username': self.username_input.text(),
            'password': self.password_input.text(),
            'port': self.port_input.value()
        }
    
    def accept(self):
        """Dialog onaylandığında"""
        # Gerekli alanları kontrol et
        if not self.ip_input.text():
            QMessageBox.warning(self, "Hata", "IP adresi boş olamaz!")
            return
        
        if not self.username_input.text():
            QMessageBox.warning(self, "Hata", "Kullanıcı adı boş olamaz!")
            return
        
        super().accept()

class ConnectionTestThread(QThread):
    test_completed = pyqtSignal(bool, str)
    
    def __init__(self, host, username, password, port):
        super().__init__()
        self.host = host
        self.username = username
        self.password = password
        self.port = port
    
    def run(self):
        """Bağlantı testi"""
        try:
            import paramiko
            import socket
            
            # Ping testi
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result != 0:
                self.test_completed.emit(False, "Cihaza ulaşılamıyor!")
                return
            
            # SSH testi
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                timeout=10
            )
            
            # Basit komut testi
            stdin, stdout, stderr = ssh.exec_command('echo "test"')
            output = stdout.read().decode().strip()
            
            ssh.close()
            
            if output == "test":
                self.test_completed.emit(True, "Bağlantı başarılı!")
            else:
                self.test_completed.emit(False, "SSH komutu çalıştırılamadı!")
                
        except Exception as e:
            self.test_completed.emit(False, f"Bağlantı hatası: {str(e)}")
