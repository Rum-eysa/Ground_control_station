# Config
# server/config.py - Sunucu konfigürasyonu
# =============================================================================

# Kamera ayarları
CAMERA_CONFIG = {
    'index': 0,           # Kamera indeksi (0 = varsayılan)
    'width': 640,         # Çözünürlük genişliği
    'height': 480,        # Çözünürlük yüksekliği
    'fps': 30,            # Frame per second
    'quality': 80,        # JPEG kalitesi (1-100)
    'buffer_size': 1      # Kamera buffer boyutu
}

# ZED kamera ayarları (Jetson için)
ZED_CONFIG = {
    'resolution': 'HD720',  # VGA, HD720, HD1080, HD2K
    'fps': 30,
    'depth_mode': 'PERFORMANCE',  # PERFORMANCE, QUALITY, ULTRA
    'quality': 80
}

# Server ayarları
SERVER_CONFIG = {
    'raspberry_port': 8888,
    'jetson_port': 8889,
    'max_clients': 5,
    'timeout': 30
}

# Logging ayarları
LOGGING_CONFIG = {
    'level': 'INFO',
    'file': '/var/log/camera_server.log',
    'max_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}