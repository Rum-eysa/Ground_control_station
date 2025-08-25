# Camera Server
# server/camera_server.py - Ana kamera sunucusu
# =============================================================================

import cv2
import socket
import threading
import time
import logging
from config import CAMERA_CONFIG

class CameraServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = []
        self.camera = None
        self.logger = logging.getLogger(__name__)
        
        # Kamera ayarları
        self.camera_config = CAMERA_CONFIG
        
    def start_server(self):
        """Sunucuyu başlat"""
        try:
            # Kamerayı başlat
            self._init_camera()
            
            # Socket sunucusunu başlat
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            self.logger.info(f"Kamera sunucusu başlatıldı: {self.host}:{self.port}")
            
            # İstemci kabul thread'i
            accept_thread = threading.Thread(target=self._accept_clients)
            accept_thread.daemon = True
            accept_thread.start()
            
            # Video streaming thread'i
            stream_thread = threading.Thread(target=self._stream_video)
            stream_thread.daemon = True
            stream_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Sunucu başlatma hatası: {e}")
            return False
    
    def _init_camera(self):
        """Kamerayı başlat"""
        try:
            camera_index = self.camera_config.get('index', 0)
            self.camera = cv2.VideoCapture(camera_index)
            
            # Kamera ayarları
            width = self.camera_config.get('width', 640)
            height = self.camera_config.get('height', 480)
            fps = self.camera_config.get('fps', 30)
            
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self.camera.set(cv2.CAP_PROP_FPS, fps)
            
            if not self.camera.isOpened():
                raise Exception("Kamera açılamadı")
            
            self.logger.info(f"Kamera başlatıldı: {width}x{height}@{fps}fps")
            
        except Exception as e:
            self.logger.error(f"Kamera başlatma hatası: {e}")
            raise
    
    def _accept_clients(self):
        """İstemci bağlantılarını kabul et"""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                self.clients.append(client_socket)
                self.logger.info(f"İstemci bağlandı: {client_address}")
                
            except Exception as e:
                if self.running:
                    self.logger.error(f"İstemci kabul hatası: {e}")
    
    def _stream_video(self):
        """Video akışını gönder"""
        while self.running and self.camera:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    continue
                
                # Frame'i encode et
                _, buffer = cv2.imencode('.jpg', frame, 
                                       [cv2.IMWRITE_JPEG_QUALITY, 
                                        self.camera_config.get('quality', 80)])
                
                frame_data = buffer.tobytes()
                frame_size = len(frame_data)
                
                # Bağlı tüm istemcilere gönder
                disconnected_clients = []
                
                for client in self.clients[:]:
                    try:
                        # Frame boyutunu gönder
                        client.send(frame_size.to_bytes(4, 'big'))
                        
                        # Frame verisini gönder
                        client.sendall(frame_data)
                        
                    except Exception as e:
                        disconnected_clients.append(client)
                        self.logger.warning(f"İstemci bağlantısı kesildi: {e}")
                
                # Bağlantısı kesilen istemcileri temizle
                for client in disconnected_clients:
                    if client in self.clients:
                        self.clients.remove(client)
                        try:
                            client.close()
                        except:
                            pass
                
                # FPS kontrolü
                time.sleep(1.0 / self.camera_config.get('fps', 30))
                
            except Exception as e:
                self.logger.error(f"Video streaming hatası: {e}")
                time.sleep(0.1)
    
    def stop_server(self):
        """Sunucuyu durdur"""
        self.running = False
        
        # İstemci bağlantılarını kapat
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        
        # Kamerayı kapat
        if self.camera:
            self.camera.release()
        
        # Sunucu socket'ini kapat
        if self.server_socket:
            self.server_socket.close()
        
        self.logger.info("Kamera sunucusu durduruldu")

if __name__ == "__main__":
    # Logging ayarla
    logging.basicConfig(level=logging.INFO)
    
    # Sunucuyu başlat
    server = CameraServer()
    
    try:
        server.start_server()
        
        # Sunucuyu çalışır durumda tut
        while server.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Sunucu durduruluyor...")
    finally:
        server.stop_server()