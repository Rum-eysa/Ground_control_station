import cv2
import socket
import threading
import struct
import time
import json
import logging
import numpy as np
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
import queue
from PyQt5.QtCore import QObject, pyqtSignal, QThread

# Logging ayarları
logger = logging.getLogger(__name__)

class CameraClient(QObject):
    # PyQt sinyalleri
    frame_received = pyqtSignal(int, np.ndarray)  # camera_id, frame
    connection_status = pyqtSignal(bool, str)     # connected, message
    error_occurred = pyqtSignal(str)              # error_message
    camera_list_updated = pyqtSignal(list)        # camera_ids
    stats_updated = pyqtSignal(dict)              # camera_stats
    
    def __init__(self, server_host="localhost", server_port=9995):
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
        self.running = False
        self.cameras = []
        self.server_info = {}
        
        # Thread-safe socket kullanımı için lock
        self.socket_lock = threading.Lock()
        
        # Her kamera için istatistikler
        self.camera_stats = {}
        self.frame_queues = {}
        
        # Bağlantı durumu
        self.connected = False
        self.main_thread_running = True
        
    def connect_to_server(self, host, port):
        """Server'a bağlan ve kamera listesini al"""
        self.server_host = host
        self.server_port = port
        
        try:
            logger.info(f"🔗 Server'a bağlanılıyor: {self.server_host}:{self.server_port}")
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1048576)
            self.socket.settimeout(10.0)
            
            self.socket.connect((self.server_host, self.server_port))
            self.connected = True
            
            self.connection_status.emit(True, "✅ Server'a bağlandı")
            logger.info("✅ Server'a bağlandı")
            
            # İlk mesajı al (kamera listesi)
            header_data = self.socket.recv(4)
            if len(header_data) != 4:
                raise Exception("Header alınamadı")
            
            msg_size = struct.unpack("!I", header_data)[0]
            
            # JSON mesajını al
            json_data = b""
            while len(json_data) < msg_size:
                chunk = self.socket.recv(msg_size - len(json_data))
                if not chunk:
                    break
                json_data += chunk
            
            camera_info = json.loads(json_data.decode('utf-8'))
            
            if camera_info['type'] == 'camera_list':
                self.cameras = camera_info['cameras']
                self.server_info = camera_info['server_info']
                
                logger.info("📋 Server bilgileri alındı:")
                logger.info(f"  🎬 FPS: {self.server_info['fps']}")
                logger.info(f"  📐 Çözünürlük: {self.server_info['resolution']}")
                logger.info(f"  💾 Kalite: {self.server_info['quality']}%")
                logger.info(f"  📹 Kameralar: {self.cameras}")
                
                # Kamera listesini sinyal ile gönder
                self.camera_list_updated.emit(self.cameras)
                
                return True
            else:
                error_msg = "❌ Geçersiz server response"
                self.error_occurred.emit(error_msg)
                logger.error(error_msg)
                return False
                
        except socket.timeout:
            error_msg = "⏱️ Bağlantı timeout"
            self.connection_status.emit(False, error_msg)
            logger.error(error_msg)
            return False
        except Exception as e:
            error_msg = f"❌ Bağlantı hatası: {e}"
            self.connection_status.emit(False, error_msg)
            logger.error(error_msg)
            return False
    
    def send_request_safe(self, request):
        """Thread-safe request gönderme"""
        try:
            with self.socket_lock:
                if not self.connected:
                    return False
                    
                request_json = json.dumps(request).encode('utf-8')
                self.socket.sendall(struct.pack("!I", len(request_json)))
                self.socket.sendall(request_json)
                return True
        except Exception as e:
            error_msg = f"❌ Request gönderim hatası: {e}"
            self.error_occurred.emit(error_msg)
            self.connected = False
            return False
    
    def receive_response_safe(self):
        """Thread-safe response alma"""
        try:
            with self.socket_lock:
                if not self.connected:
                    return None
                    
                # Header al
                header_data = self.socket.recv(4)
                if len(header_data) != 4:
                    return None
                
                header_size = struct.unpack("!I", header_data)[0]
                
                # Header JSON al
                header_json_data = b""
                while len(header_json_data) < header_size:
                    chunk = self.socket.recv(header_size - len(header_json_data))
                    if not chunk:
                        return None
                    header_json_data += chunk
                
                header = json.loads(header_json_data.decode('utf-8'))
                
                # Frame data varsa al
                if header['type'] == 'frame':
                    frame_size_data = self.socket.recv(4)
                    if len(frame_size_data) != 4:
                        return None
                    
                    frame_size = struct.unpack("!I", frame_size_data)[0]
                    
                    frame_data = b""
                    while len(frame_data) < frame_size:
                        chunk = self.socket.recv(min(frame_size - len(frame_data), 65536))
                        if not chunk:
                            return None
                        frame_data += chunk
                    
                    return {
                        'header': header,
                        'frame_data': frame_data
                    }
                else:
                    return {
                        'header': header,
                        'frame_data': None
                    }
                    
        except Exception as e:
            error_msg = f"❌ Response alma hatası: {e}"
            self.error_occurred.emit(error_msg)
            self.connected = False
            return None
    
    def frame_receiver_thread(self):
        """Tüm kameralar için frame alma thread'i"""
        logger.info("🎥 Frame receiver thread başlatılıyor...")
        
        # Her kamera için son request zamanı
        last_request_times = {camera_id: 0 for camera_id in self.cameras}
        
        # FPS kontrolü için - maksimum hız
        target_fps = self.server_info.get('fps', 30)
        frame_interval = 1.0 / (target_fps * 3)  # 3x daha hızlı request
        
        # Round-robin kamera seçimi
        camera_index = 0
        
        while self.running and self.main_thread_running and self.connected:
            try:
                current_time = time.time()
                
                if not self.cameras:
                    time.sleep(0.1)
                    continue
                
                # Hangi kameradan frame isteyeceğini belirle
                camera_id = self.cameras[camera_index % len(self.cameras)]
                camera_index += 1
                
                # Bu kameradan ne zaman son frame istendiğini kontrol et
                if current_time - last_request_times[camera_id] < frame_interval:
                    continue  # Hiç bekleme
                
                # Frame isteği gönder
                request = {
                    'type': 'get_frame',
                    'camera_id': camera_id
                }
                
                if not self.send_request_safe(request):
                    error_msg = "❌ Frame request gönderilemedi - bağlantı koptu"
                    self.error_occurred.emit(error_msg)
                    logger.error(error_msg)
                    break
                
                last_request_times[camera_id] = current_time
                
                # Response al
                response = self.receive_response_safe()
                if not response:
                    error_msg = "❌ Response alınamadı - bağlantı koptu"
                    self.error_occurred.emit(error_msg)
                    logger.error(error_msg)
                    break
                
                header = response['header']
                
                if header['type'] == 'frame' and response['frame_data']:
                    # Frame decode et
                    frame_np = np.frombuffer(response['frame_data'], dtype=np.uint8)
                    frame = cv2.imdecode(frame_np, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        # İstatistikleri güncelle
                        if camera_id not in self.camera_stats:
                            self.camera_stats[camera_id] = {
                                'frames_received': 0,
                                'fps': 0,
                                'last_fps_time': current_time,
                                'frame_count_for_fps': 0,
                                'errors': 0,
                                'last_frame_time': 0,
                                'connection_lost': False
                            }
                        
                        stats = self.camera_stats[camera_id]
                        stats['frames_received'] += 1
                        stats['frame_count_for_fps'] += 1
                        stats['last_frame_time'] = current_time
                        stats['connection_lost'] = False
                        
                        # FPS hesapla (her 5 frame'de bir - çok sık güncelle)
                        if stats['frame_count_for_fps'] >= 5:
                            fps_elapsed = current_time - stats['last_fps_time']
                            if fps_elapsed > 0:
                                stats['fps'] = 5.0 / fps_elapsed
                            stats['last_fps_time'] = current_time
                            stats['frame_count_for_fps'] = 0
                        
                        # Frame'i PyQt sinyali ile gönder
                        self.frame_received.emit(camera_id, frame)
                        
                        # İstatistikleri güncelle sinyali
                        self.stats_updated.emit(self.camera_stats)
                
                elif header['type'] == 'no_frame':
                    # Frame hazır değil, devam et
                    pass
                    
                elif header['type'] == 'error':
                    error_msg = f"❌ Server hatası: {header['message']}"
                    self.error_occurred.emit(error_msg)
                    logger.error(error_msg)
                    if camera_id in self.camera_stats:
                        self.camera_stats[camera_id]['errors'] += 1
                
            except Exception as e:
                error_msg = f"❌ Frame receiver beklenmeyen hata: {e}"
                self.error_occurred.emit(error_msg)
                logger.error(error_msg)
                if camera_id in self.camera_stats:
                    self.camera_stats[camera_id]['connection_lost'] = True
                time.sleep(0.1)
        
        logger.info("🔚 Frame receiver thread sonlandırıldı")
    
    def connect(self, host=None, port=None):
        """Bağlantıyı başlat - PyQt uyumlu"""
        if host:
            self.server_host = host
        if port:
            self.server_port = port
            
        if self.connect_to_server(self.server_host, self.server_port):
            self.running = True
            self.main_thread_running = True
            
            # Frame receiver thread'ini başlat
            receiver_thread = threading.Thread(target=self.frame_receiver_thread)
            receiver_thread.daemon = True
            receiver_thread.start()
            
            return True
        return False
    
    def disconnect(self):
        """Bağlantıyı kes - PyQt uyumlu"""
        self.running = False
        self.main_thread_running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        self.connection_status.emit(False, "Bağlantı kesildi")
        logger.info("🔌 Bağlantı kesildi")
    
    def get_camera_stats(self):
        """Kamera istatistiklerini döndür"""
        return self.camera_stats
    
    def get_available_cameras(self):
        """Mevcut kameraları döndür"""
        return self.cameras

# Standalone çalıştırma için
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='🎥 Network Multi Camera Client')
    parser.add_argument('server_ip', help='Server IP adresi')
    parser.add_argument('--port', type=int, default=9995, help='Server port numarası')
    parser.add_argument('--verbose', '-v', action='store_true', help='Detaylı log')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Client oluştur
    client = CameraClient(args.server_ip, args.port)
    
    try:
        if client.connect():
            print("✅ Client başarıyla başlatıldı")
            print("Kamera listesi:", client.get_available_cameras())
            
            # Ana döngü
            while True:
                time.sleep(1)
                stats = client.get_camera_stats()
                for cam_id, stat in stats.items():
                    print(f"Camera {cam_id}: {stat['fps']:.1f} FPS")
                    
        else:
            print("❌ Client başlatılamadı")
            
    except KeyboardInterrupt:
        print("\n⌨️ Ctrl+C ile durduruldu")
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
    finally:
        client.disconnect()
    
    print("👋 Client kapatıldı")