import json
import subprocess
import socket
import os
from datetime import datetime
from .ssh_manager import SSHManager
from .auto_discovery import AutoDiscovery
from .camera_client import CameraClient
import logging
from PyQt5.QtCore import QObject, pyqtSignal

class DeviceManager(QObject):
    device_found = pyqtSignal(dict)
    device_connected = pyqtSignal(str, str)  # device_type, ip
    device_disconnected = pyqtSignal(str, str)
    status_changed = pyqtSignal(str)
    
    def __init__(self, config_manager, logger):
        super().__init__()
        self.config_manager = config_manager
        self.logger = logger
        self.devices = {}
        self.ssh_managers = {}
        self.camera_clients = {}
        self.discovery = AutoDiscovery()
        
        # Discovery sinyallerini bağla
        self.discovery.device_found.connect(self._on_device_found)
        self.load_devices()
        
    def load_devices(self):
        """Cihazları config dosyasından yükle"""
        try:
            devices_config = self.config_manager.get_config('devices')
            self.devices = devices_config.get('devices', {})
            self.logger.info(f"{len(self.devices)} cihaz yüklendi")
        except Exception as e:
            self.logger.error(f"Cihazlar yüklenirken hata: {e}")
            
    def _on_device_found(self, device_info):
        """Bulunan cihazı kaydet"""
        ip = device_info['ip']
        self.devices[ip] = device_info
        self.device_found.emit(device_info)
        self.logger.info(f"Cihaz bulundu: {device_info}")
    
    def start_discovery(self):
        """Otomatik cihaz keşfi başlat"""
        self.status_changed.emit("Cihazlar aranıyor...")
        self.discovery.start_scan()
    
    def connect_raspberry(self, ip=None, username="rumeysa", password="her"):
        """Raspberry Pi'ye bağlan ve kamera sunucusunu başlat"""
        if ip is None:
            # Otomatik Raspberry Pi bul
            for device_ip, device_info in self.devices.items():
                if device_info.get('type') == 'raspberry':
                    ip = device_ip
                    break
        
        if not ip:
            self.status_changed.emit("Raspberry Pi bulunamadı!")
            return False
        
        try:
            # SSH bağlantısı kur
            ssh_manager = SSHManager()
            success, client, message = ssh_manager.create_ssh_connection("raspberry_pi")
            
            if success:
                self.ssh_managers[ip] = ssh_manager
                
                # Kamera sunucusunu başlat
                server_success, server_message = ssh_manager.start_camera_server("raspberry_pi")
                
                # Kamera istemcisi bağlantısı kur
                camera_client = CameraClient()
                # Burada gerçek bağlantı kodunu ekle
                
                self.device_connected.emit('raspberry', ip)
                self.status_changed.emit(f"Raspberry Pi bağlandı: {ip}")
                return True
            else:
                self.status_changed.emit(f"SSH bağlantı hatası: {message}")
                
        except Exception as e:
            self.logger.error(f"Raspberry Pi bağlantı hatası: {e}")
            self.status_changed.emit(f"Raspberry Pi bağlantı hatası: {str(e)}")
        
        return False
    
    def connect_jetson(self, ip=None, username="ika", password="0123456789"):
        """Jetson'a bağlan ve ZED kamera sunucusunu başlat"""
        if ip is None:
            # Otomatik Jetson bul
            for device_ip, device_info in self.devices.items():
                if device_info.get('type') == 'jetson':
                    ip = device_ip
                    break
        
        if not ip:
            self.status_changed.emit("Jetson bulunamadı!")
            return False
        
        try:
            # SSH bağlantısı kur
            ssh_manager = SSHManager()
            success, client, message = ssh_manager.create_ssh_connection("jetson_nano")
            
            if success:
                self.ssh_managers[ip] = ssh_manager
                
                # ZED kamera sunucusunu başlat
                server_success, server_message = ssh_manager.start_camera_server("jetson_nano")
                
                self.device_connected.emit('jetson', ip)
                self.status_changed.emit(f"Jetson bağlandı: {ip}")
                return True
            else:
                self.status_changed.emit(f"SSH bağlantı hatası: {message}")
                
        except Exception as e:
            self.logger.error(f"Jetson bağlantı hatası: {e}")
            self.status_changed.emit(f"Jetson bağlantı hatası: {str(e)}")
        
        return False
    
    def quick_recovery(self):
        """Kopan bağlantıları onar"""
        self.status_changed.emit("Bağlantılar onarılıyor...")
        
        # Tüm kayıtlı cihazlara bağlanmayı dene
        recovery_count = 0
        
        for ip, device_info in self.devices.items():
            device_type = device_info.get('type')
            
            if device_type == 'raspberry':
                if self.connect_raspberry(ip):
                    recovery_count += 1
            elif device_type == 'jetson':
                if self.connect_jetson(ip):
                    recovery_count += 1
        
        self.status_changed.emit(f"{recovery_count} cihaz kurtarıldı")
        return recovery_count
    
    def disconnect_device(self, ip):
        """Belirtilen cihazın bağlantısını kes"""
        # SSH bağlantısını kapat
        if ip in self.ssh_managers:
            self.ssh_managers[ip].close_connection("raspberry_pi" if "raspberry" in ip else "jetson_nano")
            del self.ssh_managers[ip]
        
        device_info = self.devices.get(ip, {})
        device_type = device_info.get('type', 'unknown')
        
        self.device_disconnected.emit(device_type, ip)
        self.status_changed.emit(f"Cihaz bağlantısı kesildi: {ip}")