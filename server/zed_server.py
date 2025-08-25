# Zed Server
# server/zed_server.py - ZED kamera sunucusu (Jetson için)
# =============================================================================

import cv2
import socket
import threading
import time
import logging
import numpy as np
try:
    import pyzed.sl as sl # type: ignore
    ZED_AVAILABLE = True
except ImportError:
    ZED_AVAILABLE = False
    
from config import ZED_CONFIG, SERVER_CONFIG

class ZEDServer:
    def __init__(self, host='0.0.0.0', port=8889):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = []
        self.zed = None
        self.logger = logging.getLogger(__name__)
        
        # ZED ayarları
        self.zed_config = ZED_CONFIG
        
        if not ZED_AVAILABLE:
            self.logger.error("ZED SDK bulunamadı!")
    
    def start_server(self):
        """ZED sunucusunu başlat"""
        if not ZED_AVAILABLE:
            self.logger.error("ZED SDK yüklü değil!")
            return False
        
        try:
            # ZED kamerayı başlat
            self._init_zed_camera()
            
            # Socket sunucusunu başlat
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            self.logger.info(f"ZED sunucusu başlatıldı: {self.host}:{self.port}")
            
            # İstemci kabul thread'i
            accept_thread = threading.Thread(target=self._accept_clients)
            accept_thread.daemon = True
            accept_thread.start()
            
            # Video streaming thread'i
            stream_thread = threading.Thread(target=self._stream_zed_video)
            stream_thread.daemon = True
            stream_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"ZED sunucusu başlatma hatası: {e}")
            return False
    
    def _init_zed_camera(self):
        """ZED kamerayı başlat"""
        try:
            self.zed = sl.Camera()
            
            # ZED ayarları
            init_params = sl.InitParameters()
            
            # Çözünürlük ayarı
            resolution_map = {
                'VGA': sl.RESOLUTION.VGA,
                'HD720': sl.RESOLUTION.HD720,
                'HD1080': sl.RESOLUTION.HD1080,
                'HD2K': sl.RESOLUTION.HD2K
            }
            init_params.camera_resolution = resolution_map.get(
                self.zed_config.get('resolution', 'HD720'), 
                sl.RESOLUTION.HD720
            )
            
            # FPS ayarı
            init_params.camera_fps = self.zed_config.get('fps', 30)
            
            # Derinlik modu
            depth_mode_map = {
                'PERFORMANCE': sl.DEPTH_MODE.PERFORMANCE,
                'QUALITY': sl.DEPTH_MODE.QUALITY,
                'ULTRA': sl.DEPTH_MODE.ULTRA
            }
            init_params.depth_mode = depth_mode_map.get(
                self.zed_config.get('depth_mode', 'PERFORMANCE'),
                sl.DEPTH_MODE.PERFORMANCE
            )
            
            # Kamerayı aç
            err = self.zed.open(init_params)
            if err != sl.ERROR_CODE.SUCCESS:
                raise Exception(f"ZED kamera açılamadı: {err}")
            
            self.logger.info("ZED kamera başlatıldı")
            
        except Exception as e:
            self.logger.error(f"ZED kamera başlatma hatası: {e}")
            raise
    
    def _accept_clients(self):
        """İstemci bağlantılarını kabul et"""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                self.clients.append(client_socket)
                self.logger.info(f"ZED istemcisi bağlandı: {client_address}")
                
            except Exception as e:
                if self.running:
                    self.logger.error(f"ZED istemci kabul hatası: {e}")
    
    def _stream_zed_video(self):
        """ZED video akışını gönder"""
        if not self.zed:
            return
        
        # ZED image buffer'ları
        left_image = sl.Mat()
        runtime_params = sl.RuntimeParameters()
        
        while self.running:
            try:
                # ZED'den frame al
                if self.zed.grab(runtime_params) == sl.ERROR_CODE.SUCCESS:
                    # Sol kamera görüntüsünü al
                    self.zed.retrieve_image(left_image, sl.VIEW.LEFT)
                    
                    # OpenCV formatına çevir
                    frame = left_image.get_data()
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                    
                    # Frame'i encode et
                    _, buffer = cv2.imencode('.jpg', frame, 
                                           [cv2.IMWRITE_JPEG_QUALITY, 
                                            self.zed_config.get('quality', 80)])
                    
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
                            self.logger.warning(f"ZED istemci bağlantısı kesildi: {e}")
                    
                    # Bağlantısı kesilen istemcileri temizle
                    for client in disconnected_clients:
                        if client in self.clients:
                            self.clients.remove(client)
                            try:
                                client.close()
                            except:
                                pass
                
                # FPS kontrolü
                time.sleep(1.0 / self.zed_config.get('fps', 30))
                
            except Exception as e:
                self.logger.error(f"ZED video streaming hatası: {e}")
                time.sleep(0.1)
    
    def stop_server(self):
        """ZED sunucusunu durdur"""
        self.running = False
        
        # İstemci bağlantılarını kapat
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        
        # ZED kamerayı kapat
        if self.zed:
            self.zed.close()
        
        # Sunucu socket'ini kapat
        if self.server_socket:
            self.server_socket.close()
        
        self.logger.info("ZED sunucusu durduruldu")

if __name__ == "__main__":
    # Logging ayarla
    logging.basicConfig(level=logging.INFO)
    
    # ZED sunucusunu başlat
    server = ZEDServer()
    
    try:
        if server.start_server():
            # Sunucuyu çalışır durumda tut
            while server.running:
                time.sleep(1)
        else:
            print("ZED sunucusu başlatılamadı!")
            
    except KeyboardInterrupt:
        print("ZED sunucusu durduruluyor...")
    finally:
        server.stop_server()
