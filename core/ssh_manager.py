import paramiko
import json
import os
import time
import threading
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import logging

class SSHManager:
    def __init__(self, config_path: str = "config/devices.json"):
        self.config_path = config_path
        self.devices_config = self._load_config()
        self.connections = {}
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self) -> Dict:
        """Cihaz konfigürasyonunu yükle"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Konfigürasyon dosyası bulunamadı: {self.config_path}")
            return {"devices": {}}
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode hatası: {e}")
            return {"devices": {}}
    
    def get_device_config(self, device_name: str) -> Optional[Dict]:
        """Cihaz konfigürasyonunu getir"""
        return self.devices_config.get("devices", {}).get(device_name)
    
    def create_ssh_connection(self, device_name: str) -> Tuple[bool, Optional[paramiko.SSHClient], str]:
        """SSH bağlantısı oluştur"""
        device_config = self.get_device_config(device_name)
        if not device_config:
            return False, None, f"Cihaz konfigürasyonu bulunamadı: {device_name}"
        
        connection_info = device_config.get("connection", {})
        
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Bağlantı parametreleri - önce IP, sonra hostname dene
            host = connection_info.get("ip") or connection_info.get("host")
            port = connection_info.get("port", 22)
            username = connection_info.get("username")
            password = connection_info.get("password")
            ssh_key_path = connection_info.get("ssh_key_path")
            
            timeout = self.devices_config.get("connection_settings", {}).get("timeout", 30)
            
            # Hostname varsa ve IP yoksa, hostname kullan
            if not connection_info.get("ip") and connection_info.get("host"):
                host = connection_info.get("host")
                self.logger.info(f"Hostname kullanılıyor: {host}")
            
            # SSH key varsa onu kullan, yoksa şifre
            if ssh_key_path and os.path.exists(ssh_key_path):
                client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    key_filename=ssh_key_path,
                    timeout=timeout
                )
                self.logger.info(f"SSH key ile bağlandı: {device_name}")
            else:
                client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password=password,
                    timeout=timeout
                )
                self.logger.info(f"Şifre ile bağlandı: {device_name}")
            
            # Bağlantıyı sakla
            self.connections[device_name] = client
            return True, client, "Bağlantı başarılı"
            
        except paramiko.AuthenticationException:
            return False, None, "Kimlik doğrulama hatası"
        except paramiko.SSHException as e:
            return False, None, f"SSH hatası: {str(e)}"
        except Exception as e:
            return False, None, f"Bağlantı hatası: {str(e)}"
    
    def execute_command(self, device_name: str, command: str) -> Tuple[bool, str, str]:
        """SSH üzerinden komut çalıştır"""
        client = self.connections.get(device_name)
        if not client:
            success, client, message = self.create_ssh_connection(device_name)
            if not success:
                return False, "", message
        
        try:
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            return True, output, error
            
        except Exception as e:
            return False, "", f"Komut çalıştırma hatası: {str(e)}"
    
    def start_camera_server(self, device_name: str) -> Tuple[bool, str]:
        """Kamera sunucusunu başlat"""
        device_config = self.get_device_config(device_name)
        if not device_config:
            return False, "Cihaz konfigürasyonu bulunamadı"
        
        services = device_config.get("services", {})
        server_script = services.get("camera_server")
        
        if not server_script:
            return False, "Sunucu scripti tanımlanmamış"
        
        # Sunucuyu arka planda başlat
        command = f"cd /home/{device_config['connection']['username']} && python3 {server_script} &"
        
        success, output, error = self.execute_command(device_name, command)
        
        if success:
            return True, f"Sunucu başlatıldı: {server_script}"
        else:
            return False, f"Sunucu başlatma hatası: {error}"
    
    def close_connection(self, device_name: str):
        """Bağlantıyı kapat"""
        if device_name in self.connections:
            self.connections[device_name].close()
            del self.connections[device_name]
            self.logger.info(f"Bağlantı kapatıldı: {device_name}")