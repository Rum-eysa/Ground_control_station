import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import shutil
from datetime import datetime

class ConfigManager:
    """Konfigürasyon dosyalarını yönetir"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Ana konfigürasyon dosyaları
        self.devices_config_path = self.config_dir / "devices.json"
        self.settings_config_path = self.config_dir / "settings.json"
        self.camera_config_path = self.config_dir / "camera_config.json"
        self.network_config_path = self.config_dir / "network_config.json"
        
        # Konfigürasyonları yükle
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Tüm konfigürasyon dosyalarını yükle"""
        self.devices_config = self._load_config(self.devices_config_path, self._get_default_devices_config())
        self.settings_config = self._load_config(self.settings_config_path, self._get_default_settings())
        self.camera_config = self._load_config(self.camera_config_path, self._get_default_camera_config())
        self.network_config = self._load_config(self.network_config_path, self._get_default_network_config())
    
    def _load_config(self, config_path: Path, default_config: Dict) -> Dict:
        """Bir konfigürasyon dosyasını yükle"""
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Varsayılan değerlerle birleştir
                    return self._merge_configs(default_config, config)
            else:
                # Dosya yoksa varsayılan konfigürasyonu oluştur
                self._save_config(config_path, default_config)
                return default_config.copy()
        except Exception as e:
            self.logger.error(f"Konfigürasyon yükleme hatası {config_path}: {e}")
            return default_config.copy()
    
    def _save_config(self, config_path: Path, config: Dict):
        """Konfigürasyonu dosyaya kaydet"""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Konfigürasyon kaydetme hatası {config_path}: {e}")
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """İki konfigürasyonu birleştir (user config öncelikli)"""
        result = default.copy()
        for key, value in user.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _get_default_devices_config(self) -> Dict:
        """Varsayılan cihaz konfigürasyonu"""
        return {
            "devices": {
                "raspberry_pi": {
                    "name": "Raspberry Pi Camera",
                    "type": "raspberry_pi",
                    "connection": {
                        "host": "raspberrypi",
                        "ip": "192.168.68.100",
                        "port": 22,
                        "username": "rumeysa",
                        "password": "her",
                        "auth_method": "password",
                        "ssh_key_path": None
                    },
                    "camera": {
                        "stream_port": 5000,
                        "control_port": 5001,
                        "resolution": [1920, 1080],
                        "fps": 30
                    },
                    "services": {
                        "camera_server": "camera_server.py",
                        "auto_start": True,
                        "health_check_port": 5002
                    }
                },
                "jetson_nano": {
                    "name": "Jetson Nano (ika) ZED Camera",
                    "type": "jetson",
                    "connection": {
                        "host": "ika",
                        "ip": "192.168.68.101",
                        "port": 22,
                        "username": "ika",
                        "password": "0123456789",
                        "auth_method": "password",
                        "ssh_key_path": None
                    },
                    "camera": {
                        "stream_port": 6000,
                        "control_port": 6001,
                        "resolution": [2208, 1242],
                        "fps": 30,
                        "camera_type": "zed"
                    },
                    "services": {
                        "camera_server": "zed_server.py",
                        "auto_start": True,
                        "health_check_port": 6002
                    }
                }
            },
            "connection_settings": {
                "timeout": 30,
                "retry_attempts": 3,
                "retry_delay": 5,
                "keep_alive_interval": 30,
                "compression": True
            },
            "security": {
                "encrypt_passwords": False,
                "ssh_key_preference": True,
                "known_hosts_check": False
            }
        }
    
    def _get_default_settings(self) -> Dict:
        """Varsayılan genel ayarlar"""
        return {
            "application": {
                "theme": "dark",
                "language": "tr",
                "auto_connect": True,
                "minimize_to_tray": True,
                "start_minimized": False
            },
            "logging": {
                "level": "INFO",
                "max_file_size": "10MB",
                "backup_count": 5,
                "console_output": True
            },
            "gui": {
                "window_size": [1200, 800],
                "window_position": [100, 100],
                "remember_window_state": True,
                "show_toolbar": True,
                "show_statusbar": True
            },
            "video": {
                "auto_record": False,
                "record_format": "mp4",
                "record_quality": "high",
                "max_record_duration": 3600
            }
        }
    
    def _get_default_camera_config(self) -> Dict:
        """Varsayılan kamera ayarları"""
        return {
            "raspberry_pi": {
                "resolution": [1920, 1080],
                "fps": 30,
                "format": "MJPEG",
                "brightness": 50,
                "contrast": 50,
                "saturation": 50,
                "auto_exposure": True,
                "exposure_compensation": 0,
                "white_balance": "auto"
            },
            "jetson_zed": {
                "resolution": [2208, 1242],
                "fps": 30,
                "depth_mode": "PERFORMANCE",
                "coordinate_units": "METER",
                "sensing_mode": "STANDARD",
                "brightness": 4,
                "contrast": 4,
                "hue": 0,
                "saturation": 4,
                "sharpness": 4,
                "gamma": 8
            },
            "stream_settings": {
                "buffer_size": 3,
                "compression_quality": 80,
                "enable_audio": False,
                "audio_bitrate": 128
            }
        }
    
    def _get_default_network_config(self) -> Dict:
        """Varsayılan ağ ayarları"""
        return {
            "discovery": {
                "enabled": True,
                "scan_range": "192.168.68.0/24",
                "scan_timeout": 5,
                "auto_update_ips": True
            },
            "connection": {
                "timeout": 30,
                "retry_attempts": 3,
                "retry_delay": 5,
                "keep_alive": True,
                "keep_alive_interval": 30
            },
            "ports": {
                "ssh": 22,
                "raspberry_stream": 5000,
                "raspberry_control": 5001,
                "jetson_stream": 6000,
                "jetson_control": 6001
            }
        }
    
    # Getter metodları
    def get_devices_config(self) -> Dict:
        """Cihaz konfigürasyonunu getir"""
        return self.devices_config
    
    def get_device_config(self, device_name: str) -> Optional[Dict]:
        """Belirli bir cihazın konfigürasyonunu getir"""
        return self.devices_config.get("devices", {}).get(device_name)
    
    def get_settings(self) -> Dict:
        """Genel ayarları getir"""
        return self.settings_config
    
    def get_camera_config(self) -> Dict:
        """Kamera ayarlarını getir"""
        return self.camera_config
    
    def get_network_config(self) -> Dict:
        """Ağ ayarlarını getir"""
        return self.network_config
    
    # Setter metodları
    def update_device_config(self, device_name: str, config: Dict):
        """Cihaz konfigürasyonunu güncelle"""
        if "devices" not in self.devices_config:
            self.devices_config["devices"] = {}
        
        self.devices_config["devices"][device_name] = config
        self._save_config(self.devices_config_path, self.devices_config)
    
    def update_device_ip(self, device_name: str, ip: str):
        """Cihazın IP adresini güncelle"""
        if device_name in self.devices_config.get("devices", {}):
            self.devices_config["devices"][device_name]["connection"]["ip"] = ip
            self._save_config(self.devices_config_path, self.devices_config)
            self.logger.info(f"IP güncellendi {device_name}: {ip}")
    
    def update_settings(self, settings: Dict):
        """Genel ayarları güncelle"""
        self.settings_config = self._merge_configs(self.settings_config, settings)
        self._save_config(self.settings_config_path, self.settings_config)
    
    def update_camera_config(self, camera_config: Dict):
        """Kamera ayarlarını güncelle"""
        self.camera_config = self._merge_configs(self.camera_config, camera_config)
        self._save_config(self.camera_config_path, self.camera_config)
    
    def update_network_config(self, network_config: Dict):
        """Ağ ayarlarını güncelle"""
        self.network_config = self._merge_configs(self.network_config, network_config)
        self._save_config(self.network_config_path, self.network_config)
    
    # Yedekleme ve geri yükleme
    def backup_configs(self, backup_dir: str = "data/backups") -> str:
        """Tüm konfigürasyonları yedekle"""
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"config_backup_{timestamp}.tar.gz"
        backup_filepath = backup_path / backup_filename
        
        try:
            # Tar arşivi oluştur
            import tarfile
            with tarfile.open(backup_filepath, "w:gz") as tar:
                tar.add(self.config_dir, arcname="config")
            
            self.logger.info(f"Konfigürasyon yedeklendi: {backup_filepath}")
            return str(backup_filepath)
            
        except Exception as e:
            self.logger.error(f"Yedekleme hatası: {e}")
            return ""
    
    def restore_configs(self, backup_filepath: str) -> bool:
        """Konfigürasyonları yedekten geri yükle"""
        try:
            import tarfile
            
            # Mevcut config'i yedekle
            current_backup = self.backup_configs("data/backups/restore_backup")
            
            # Yeni config'i çıkart
            with tarfile.open(backup_filepath, "r:gz") as tar:
                tar.extractall(path=self.config_dir.parent)
            
            # Konfigürasyonları yeniden yükle
            self._load_all_configs()
            
            self.logger.info(f"Konfigürasyon geri yüklendi: {backup_filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Geri yükleme hatası: {e}")
            return False
    
    def reset_to_defaults(self):
        """Tüm konfigürasyonları varsayılana sıfırla"""
        try:
            # Yedek al
            self.backup_configs("data/backups/reset_backup")
            
            # Varsayılan konfigürasyonları yükle
            self.devices_config = self._get_default_devices_config()
            self.settings_config = self._get_default_settings()
            self.camera_config = self._get_default_camera_config()
            self.network_config = self._get_default_network_config()
            
            # Dosyalara kaydet
            self._save_config(self.devices_config_path, self.devices_config)
            self._save_config(self.settings_config_path, self.settings_config)
            self._save_config(self.camera_config_path, self.camera_config)
            self._save_config(self.network_config_path, self.network_config)
            
            self.logger.info("Konfigürasyon varsayılana sıfırlandı")
            return True
            
        except Exception as e:
            self.logger.error(f"Sıfırlama hatası: {e}")
            return False
    
    def validate_config(self) -> Dict[str, bool]:
        """Konfigürasyon dosyalarını doğrula"""
        validation_results = {}
        
        # Devices config doğrulama
        try:
            devices = self.devices_config.get("devices", {})
            for device_name, device_config in devices.items():
                connection = device_config.get("connection", {})
                required_fields = ["host", "username", "password"]
                
                valid = all(field in connection for field in required_fields)
                validation_results[f"device_{device_name}"] = valid
                
            validation_results["devices_config"] = True
        except:
            validation_results["devices_config"] = False
        
        # Settings config doğrulama
        try:
            required_sections = ["application", "logging", "gui"]
            valid = all(section in self.settings_config for section in required_sections)
            validation_results["settings_config"] = valid
        except:
            validation_results["settings_config"] = False
        
        return validation_results


# Kullanım örneği
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    config_manager = ConfigManager()
    
    # Konfigürasyon bilgilerini göster
    print("Mevcut cihazlar:")
    devices = config_manager.get_devices_config().get("devices", {})
    for name, info in devices.items():
        connection = info.get("connection", {})
        print(f"  {name}: {connection.get('username', 'unknown')}@{connection.get('host', 'unknown')}")
    
    # Doğrulama testi
    validation = config_manager.validate_config()
    print(f"\nKonfigürasyon doğrulaması:")
    for key, valid in validation.items():
        print(f"  {key}: {'✓' if valid else '❌'}")