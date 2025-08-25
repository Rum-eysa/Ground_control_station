# Health Monitor
# core/health_monitor.py - Sistem sağlık kontrolü
# =============================================================================

import psutil
import time
import threading
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import logging

class HealthMonitor(QObject):
    health_update = pyqtSignal(dict)
    alert_triggered = pyqtSignal(str, str)  # level, message
    
    def __init__(self):
        super().__init__()
        self.monitoring = False
        self.logger = logging.getLogger(__name__)
        
        # Thresholds
        self.cpu_threshold = 80.0
        self.memory_threshold = 85.0
        self.disk_threshold = 90.0
        self.temperature_threshold = 75.0
        
        # Monitoring timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_system_health)
        
        # Last values for comparison
        self.last_values = {}
    
    def start_monitoring(self, interval=5000):  # 5 seconds
        """Sistem izlemeyi başlat"""
        if not self.monitoring:
            self.monitoring = True
            self.timer.start(interval)
            self.logger.info("Sistem sağlık izleme başlatıldı")
    
    def stop_monitoring(self):
        """Sistem izlemeyi durdur"""
        self.monitoring = False
        self.timer.stop()
        self.logger.info("Sistem sağlık izleme durduruldu")
    
    def check_system_health(self):
        """Sistem sağlığını kontrol et"""
        try:
            health_data = self.collect_health_data()
            
            # Alert kontrolü
            self.check_alerts(health_data)
            
            # Sinyal gönder
            self.health_update.emit(health_data)
            
        except Exception as e:
            self.logger.error(f"Sistem sağlık kontrolü hatası: {e}")
    
    def collect_health_data(self):
        """Sistem sağlık verilerini topla"""
        data = {}
        
        # CPU usage
        data['cpu_percent'] = psutil.cpu_percent(interval=1)
        data['cpu_count'] = psutil.cpu_count()
        data['cpu_freq'] = psutil.cpu_freq().current if psutil.cpu_freq() else 0
        
        # Memory usage
        memory = psutil.virtual_memory()
        data['memory_percent'] = memory.percent
        data['memory_available'] = memory.available // (1024*1024)  # MB
        data['memory_total'] = memory.total // (1024*1024)  # MB
        
        # Disk usage
        disk = psutil.disk_usage('/')
        data['disk_percent'] = (disk.used / disk.total) * 100
        data['disk_free'] = disk.free // (1024*1024*1024)  # GB
        data['disk_total'] = disk.total // (1024*1024*1024)  # GB
        
        # Network
        network = psutil.net_io_counters()
        data['network_bytes_sent'] = network.bytes_sent
        data['network_bytes_recv'] = network.bytes_recv
        
        # Temperature (if available)
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                # Get first available temperature
                for name, entries in temps.items():
                    if entries:
                        data['temperature'] = entries[0].current
                        break
        except:
            data['temperature'] = None
        
        # Process count
        data['process_count'] = len(psutil.pids())
        
        # Load average (Unix/Linux)
        try:
            load_avg = psutil.getloadavg()
            data['load_avg_1m'] = load_avg[0]
            data['load_avg_5m'] = load_avg[1]
            data['load_avg_15m'] = load_avg[2]
        except:
            data['load_avg_1m'] = 0
            data['load_avg_5m'] = 0
            data['load_avg_15m'] = 0
        
        # Boot time
        data['boot_time'] = psutil.boot_time()
        data['uptime'] = time.time() - psutil.boot_time()
        
        return data
    
    def check_alerts(self, health_data):
        """Alert kontrollerini yap"""
        # CPU alert
        cpu_percent = health_data.get('cpu_percent', 0)
        if cpu_percent > self.cpu_threshold:
            self.alert_triggered.emit(
                'warning',
                f"Yüksek CPU kullanımı: {cpu_percent:.1f}%"
            )
        
        # Memory alert
        memory_percent = health_data.get('memory_percent', 0)
        if memory_percent > self.memory_threshold:
            self.alert_triggered.emit(
                'warning', 
                f"Yüksek RAM kullanımı: {memory_percent:.1f}%"
            )
        
        # Disk alert
        disk_percent = health_data.get('disk_percent', 0)
        if disk_percent > self.disk_threshold:
            self.alert_triggered.emit(
                'critical',
                f"Disk alanı kritik: {disk_percent:.1f}%"
            )
        
        # Temperature alert
        temperature = health_data.get('temperature')
        if temperature and temperature > self.temperature_threshold:
            self.alert_triggered.emit(
                'warning',
                f"Yüksek sıcaklık: {temperature:.1f}°C"
            )
    
    def get_system_summary(self):
        """Sistem özetini al"""
        try:
            data = self.collect_health_data()
            
            summary = {
                'status': 'healthy',
                'cpu': f"{data['cpu_percent']:.1f}%",
                'memory': f"{data['memory_percent']:.1f}%",
                'disk': f"{data['disk_percent']:.1f}%",
                'uptime': f"{data['uptime']//3600:.0f} saat"
            }
            
            # Durum belirleme
            if (data['cpu_percent'] > self.cpu_threshold or 
                data['memory_percent'] > self.memory_threshold):
                summary['status'] = 'warning'
            
            if data['disk_percent'] > self.disk_threshold:
                summary['status'] = 'critical'
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Sistem özeti alma hatası: {e}")
            return {'status': 'error', 'message': str(e)}