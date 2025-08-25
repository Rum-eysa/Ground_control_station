import socket
import subprocess
import threading
import time
import json
import logging
from typing import Dict, List, Optional, Tuple
import ipaddress
import paramiko
from PyQt5.QtCore import QObject, pyqtSignal

class DeviceDiscovery(QObject):
    """Ağdaki cihazları otomatik keşfeden sınıf"""
    
    device_found = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.discovered_devices = {}
        
    def get_network_range(self) -> str:
        """Mevcut ağ aralığını otomatik tespit et"""
        try:
            # Windows için
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            if "192.168.68." in result.stdout:
                return "192.168.68.0/24"
            
            # Linux/Mac için
            result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if '192.168.68.' in line and 'src' in line:
                    return "192.168.68.0/24"
            
            # Fallback - varsayılan aralık
            return "192.168.68.0/24"
            
        except Exception as e:
            self.logger.warning(f"Ağ aralığı tespit edilemedi: {e}")
            return "192.168.68.0/24"
    
    def ping_host(self, ip: str) -> bool:
        """Bir IP adresini ping ile kontrol et"""
        try:
            # Windows
            result = subprocess.run(
                ['ping', '-n', '1', '-w', '1000', ip],
                capture_output=True,
                text=True,
                timeout=3
            )
            return result.returncode == 0
        except:
            try:
                # Linux/Mac
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', '1', ip],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                return result.returncode == 0
            except:
                return False
    
    def scan_port(self, ip: str, port: int, timeout: float = 1.0) -> bool:
        """Belirtilen port açık mı kontrol et"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def try_ssh_connection(self, ip: str, username: str, password: str) -> Tuple[bool, str]:
        """SSH bağlantısını test et"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            client.connect(
                hostname=ip,
                username=username,
                password=password,
                timeout=5
            )
            
            # Hostname'i al
            stdin, stdout, stderr = client.exec_command('hostname')
            hostname = stdout.read().decode().strip()
            
            client.close()
            return True, hostname
            
        except paramiko.AuthenticationException:
            return False, "Authentication failed"
        except Exception as e:
            return False, str(e)
    
    def discover_specific_devices(self) -> Dict[str, Dict]:
        """Bilinen cihazları keşfet"""
        network_range = self.get_network_range()
        self.logger.info(f"Cihaz keşfi başlatılıyor: {network_range}")
        
        discovered = {}
        
        # Raspberry Pi keşfi
        raspberry_found = self._discover_raspberry_pi(network_range)
        if raspberry_found:
            discovered['raspberry_pi'] = raspberry_found
        
        # Jetson keşfi
        jetson_found = self._discover_jetson(network_range)
        if jetson_found:
            discovered['jetson_nano'] = jetson_found
        
        self.discovered_devices = discovered
        return discovered
    
    def _discover_raspberry_pi(self, network_range: str) -> Optional[Dict]:
        """Raspberry Pi'yi keşfet"""
        self.logger.info("Raspberry Pi aranıyor...")
        
        # Önce hostname ile dene
        if self.ping_host("raspberrypi"):
            ip = self._resolve_hostname("raspberrypi")
            if ip and self.scan_port(ip, 22):
                ssh_success, hostname = self.try_ssh_connection(ip, "rumeysa", "her")
                if ssh_success:
                    self.logger.info(f"Raspberry Pi bulundu: {ip} ({hostname})")
                    device_info = {
                        "ip": ip,
                        "hostname": hostname,
                        "username": "rumeysa",
                        "auth_verified": True,
                        "type": "raspberry"
                    }
                    self.device_found.emit(device_info)
                    return device_info
        
        # IP aralığında tara
        network = ipaddress.ip_network(network_range, strict=False)
        for ip in network.hosts():
            ip_str = str(ip)
            if self.ping_host(ip_str) and self.scan_port(ip_str, 22):
                ssh_success, hostname = self.try_ssh_connection(ip_str, "rumeysa", "her")
                if ssh_success and ("raspberrypi" in hostname.lower() or "raspberry" in hostname.lower()):
                    self.logger.info(f"Raspberry Pi bulundu: {ip_str} ({hostname})")
                    device_info = {
                        "ip": ip_str,
                        "hostname": hostname,
                        "username": "rumeysa",
                        "auth_verified": True,
                        "type": "raspberry"
                    }
                    self.device_found.emit(device_info)
                    return device_info
        
        self.logger.warning("Raspberry Pi bulunamadı")
        return None
    
    def _discover_jetson(self, network_range: str) -> Optional[Dict]:
        """Jetson Nano'yu keşfet"""
        self.logger.info("Jetson Nano (ika) aranıyor...")
        
        # Önce hostname ile dene
        if self.ping_host("ika"):
            ip = self._resolve_hostname("ika")
            if ip and self.scan_port(ip, 22):
                ssh_success, hostname = self.try_ssh_connection(ip, "ika", "0123456789")
                if ssh_success:
                    self.logger.info(f"Jetson Nano bulundu: {ip} ({hostname})")
                    device_info = {
                        "ip": ip,
                        "hostname": hostname,
                        "username": "ika",
                        "auth_verified": True,
                        "type": "jetson"
                    }
                    self.device_found.emit(device_info)
                    return device_info
        
        # IP aralığında tara
        network = ipaddress.ip_network(network_range, strict=False)
        for ip in network.hosts():
            ip_str = str(ip)
            if self.ping_host(ip_str) and self.scan_port(ip_str, 22):
                ssh_success, hostname = self.try_ssh_connection(ip_str, "ika", "0123456789")
                if ssh_success:
                    self.logger.info(f"Jetson Nano bulundu: {ip_str} ({hostname})")
                    device_info = {
                        "ip": ip_str,
                        "hostname": hostname,
                        "username": "ika",
                        "auth_verified": True,
                        "type": "jetson"
                    }
                    self.device_found.emit(device_info)
                    return device_info
        
        self.logger.warning("Jetson Nano (ika) bulunamadı")
        return None
    
    def _resolve_hostname(self, hostname: str) -> Optional[str]:
        """Hostname'i IP'ye çevir"""
        try:
            return socket.gethostbyname(hostname)
        except socket.gaierror:
            return None
    
    def start_scan(self):
        """Tarama işlemini thread'de başlat"""
        thread = threading.Thread(target=self.discover_specific_devices)
        thread.daemon = True
        thread.start()

# Backward compatibility için alias
AutoDiscovery = DeviceDiscovery