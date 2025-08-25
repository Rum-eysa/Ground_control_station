import time
import threading
import logging
from typing import Dict, List, Callable
from PyQt5.QtCore import QObject, pyqtSignal
from core.ssh_manager import SSHManager
from core.config_manager import ConfigManager

class ServerLauncher(QObject):
    """Otomatik sunucu başlatıcı ve yöneticisi"""
    
    # Qt sinyalleri
    connection_status_changed = pyqtSignal(str, bool, str)  # device_name, success, message
    server_status_changed = pyqtSignal(str, bool, str)  # device_name, running, message
    deployment_status_changed = pyqtSignal(str, bool, str)  # device_name, success, message
    
    def __init__(self, config_manager: ConfigManager = None):
        super().__init__()
        self.config_manager = config_manager or ConfigManager()
        self.ssh_manager = SSHManager()
        self.logger = logging.getLogger(__name__)
        
        # Durum takibi
        self.device_statuses = {}
        self.monitoring_threads = {}
        self.is_monitoring = False
        
    def auto_launch_all(self) -> Dict[str, Dict]:
        """Tüm cihazlara otomatik bağlan ve sunucuları başlat"""
        results = {}
        devices = self.ssh_manager.devices_config.get("devices", {})
        
        for device_name, device_config in devices.items():
            results[device_name] = self._launch_device_server(device_name)
            
        return results
    
    def _launch_device_server(self, device_name: str) -> Dict:
        """Tek bir cihaz için sunucu başlatma işlemi"""
        result = {
            "connection": {"success": False, "message": ""},
            "server": {"success": False, "message": ""},
            "deployment": {"success": False, "message": ""}
        }
        
        self.logger.info(f"Cihaz başlatma işlemi başladı: {device_name}")
        
        # 1. SSH Bağlantısı
        conn_success, client, conn_message = self.ssh_manager.create_ssh_connection(device_name)
        result["connection"] = {"success": conn_success, "message": conn_message}
        self.connection_status_changed.emit(device_name, conn_success, conn_message)
        
        if not conn_success:
            return result
        
        # 2. Sunucu durumunu kontrol et
        running, status_message = self.ssh_manager.check_server_status(device_name)
        
        if not running:
            # 3. Sunucu dosyalarını kopyala (gerekirse)
            deploy_success, deploy_message = self.ssh_manager.deploy_server_files(device_name)
            result["deployment"] = {"success": deploy_success, "message": deploy_message}
            self.deployment_status_changed.emit(device_name, deploy_success, deploy_message)
            
            if not deploy_success:
                self.logger.warning(f"Dosya kopyalama başarısız, mevcut dosyalarla devam ediliyor: {device_name}")
            
            # 4. Sunucuyu başlat
            server_success, server_message = self.ssh_manager.start_camera_server(device_name)
            result["server"] = {"success": server_success, "message": server_message}
            self.server_status_changed.emit(device_name, server_success, server_message)
            
            if server_success:
                # Sunucunun başlamasını bekle
                time.sleep(3)
                # Durumu tekrar kontrol et
                running, status_message = self.ssh_manager.check_server_status(device_name)
                result["server"]["message"] = status_message
        else:
            result["server"] = {"success": True, "message": "Sunucu zaten çalışıyor"}
            self.server_status_changed.emit(device_name, True, "Sunucu zaten çalışıyor")
        
        # Durum güncelle
        self.device_statuses[device_name] = {
            "connected": conn_success,
            "server_running": running,
            "last_check": time.time()
        }
        
        return result
    
    def start_monitoring(self, check_interval: int = 30):
        """Cihaz durumu izlemeyi başlat"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.logger.info("Cihaz durumu izleme başlatıldı")
        
        for device_name in self.ssh_manager.devices_config.get("devices", {}):
            thread = threading.Thread(
                target=self._monitor_device,
                args=(device_name, check_interval),
                daemon=True
            )
            thread.start()
            self.monitoring_threads[device_name] = thread
    
    def stop_monitoring(self):
        """Cihaz durumu izlemeyi durdur"""
        self.is_monitoring = False
        self.logger.info("Cihaz durumu izleme durduruldu")
        
        # Thread'lerin bitmesini bekle
        for thread in self.monitoring_threads.values():
            if thread.is_alive():
                thread.join(timeout=5)
        
        self.monitoring_threads.clear()
    
    def _monitor_device(self, device_name: str, check_interval: int):
        """Tek bir cihazı sürekli izle"""
        while self.is_monitoring:
            try:
                # Sunucu durumunu kontrol et
                running, status_message = self.ssh_manager.check_server_status(device_name)
                
                # Durum değişikliği varsa sinyal gönder
                current_status = self.device_statuses.get(device_name, {})
                if current_status.get("server_running") != running:
                    self.server_status_changed.emit(device_name, running, status_message)
                
                # Durum güncelle
                self.device_statuses[device_name] = {
                    "connected": True,
                    "server_running": running,
                    "last_check": time.time()
                }
                
                # Sunucu çalışmıyorsa otomatik başlat
                if not running:
                    device_config = self.ssh_manager.get_device_config(device_name)
                    if device_config and device_config.get("services", {}).get("auto_start", False):
                        self.logger.warning(f"Sunucu çalışmıyor, otomatik başlatılıyor: {device_name}")
                        server_success, server_message = self.ssh_manager.start_camera_server(device_name)
                        self.server_status_changed.emit(device_name, server_success, server_message)
                
            except Exception as e:
                self.logger.error(f"İzleme hatası {device_name}: {str(e)}")
                # Bağlantı hatası durumunda yeniden bağlanmayı dene
                conn_success, client, conn_message = self.ssh_manager.create_ssh_connection(device_name)
                if not conn_success:
                    self.connection_status_changed.emit(device_name, False, conn_message)
            
            time.sleep(check_interval)
    
    def restart_server(self, device_name: str) -> Dict[str, str]:
        """Sunucuyu yeniden başlat"""
        result = {}
        
        # Önce durdur
        stop_success, stop_message = self.ssh_manager.stop_camera_server(device_name)
        result["stop"] = stop_message
        
        if stop_success:
            time.sleep(2)  # Kısa bekleme
            
            # Sonra başlat
            start_success, start_message = self.ssh_manager.start_camera_server(device_name)
            result["start"] = start_message
            
            self.server_status_changed.emit(device_name, start_success, start_message)
        
        return result
    
    def get_device_status(self, device_name: str) -> Dict:
        """Cihaz durumunu getir"""
        status = self.device_statuses.get(device_name, {})
        
        # Gerçek zamanlı kontrol
        if device_name in self.ssh_manager.connections:
            running, message = self.ssh_manager.check_server_status(device_name)
            status.update({
                "server_running": running,
                "last_message": message,
                "last_check": time.time()
            })
        
        return status
    
    def get_all_device_statuses(self) -> Dict[str, Dict]:
        """Tüm cihaz durumlarını getir"""
        statuses = {}
        for device_name in self.ssh_manager.devices_config.get("devices", {}):
            statuses[device_name] = self.get_device_status(device_name)
        return statuses
    
    def deploy_to_device(self, device_name: str, force: bool = False) -> Dict[str, str]:
        """Belirli bir cihaza dosyaları kopyala"""
        if not force:
            # Önce sunucuyu durdur
            self.ssh_manager.stop_camera_server(device_name)
            time.sleep(1)
        
        # Dosyaları kopyala
        success, message = self.ssh_manager.deploy_server_files(device_name)
        self.deployment_status_changed.emit(device_name, success, message)
        
        if success and not force:
            # Sunucuyu yeniden başlat
            time.sleep(1)
            start_success, start_message = self.ssh_manager.start_camera_server(device_name)
            return {
                "deployment": message,
                "restart": start_message
            }
        
        return {"deployment": message}
    
    def emergency_shutdown_all(self):
        """Acil durum - tüm sunucuları durdur"""
        self.logger.warning("ACİL DURUM: Tüm sunucular durduruluyor")
        
        for device_name in self.ssh_manager.devices_config.get("devices", {}):
            try:
                success, message = self.ssh_manager.stop_camera_server(device_name)
                self.server_status_changed.emit(device_name, False, f"ACİL DURDURMA: {message}")
            except Exception as e:
                self.logger.error(f"Acil durdurma hatası {device_name}: {str(e)}")
    
    def cleanup(self):
        """Temizlik işlemleri"""
        self.stop_monitoring()
        self.ssh_manager.close_all_connections()


# Kullanım örneği
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    launcher = ServerLauncher()
    
    # Tüm cihazlara bağlan ve sunucuları başlat
    results = launcher.auto_launch_all()
    
    for device_name, result in results.items():
        print(f"\n{device_name}:")
        print(f"  Bağlantı: {result['connection']['message']}")
        print(f"  Sunucu: {result['server']['message']}")
        if result['deployment']['message']:
            print(f"  Dosya Kopyalama: {result['deployment']['message']}")
    
    # İzlemeyi başlat
    launcher.start_monitoring(check_interval=30)
    
    # Test için biraz bekle
    time.sleep(60)
    
    # Temizlik
    launcher.cleanup()