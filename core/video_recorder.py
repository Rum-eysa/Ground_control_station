# Video Recorder
# core/video_recorder.py - Video kayıt sistemi
# =============================================================================

import cv2
import os
import time
import threading
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
import logging

class VideoRecorder(QObject):
    recording_started = pyqtSignal(str)  # filename
    recording_stopped = pyqtSignal(str)  # filename
    recording_error = pyqtSignal(str)    # error message
    
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.video_writer = None
        self.current_filename = None
        self.frame_queue = []
        self.recording_thread = None
        self.logger = logging.getLogger(__name__)
        
        # Kayıt ayarları
        self.output_dir = "data/recordings"
        self.codec = cv2.VideoWriter_fourcc(*'mp4v')
        self.fps = 30.0
        
        # Dizin oluştur
        os.makedirs(self.output_dir, exist_ok=True)
    
    def start_recording(self, frame_shape, filename=None):
        """Video kaydını başlat"""
        if self.is_recording:
            self.logger.warning("Kayıt zaten devam ediyor!")
            return False
        
        try:
            # Dosya adı oluştur
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"recording_{timestamp}.mp4"
            
            self.current_filename = os.path.join(self.output_dir, filename)
            
            # Video writer oluştur
            height, width = frame_shape[:2]
            self.video_writer = cv2.VideoWriter(
                self.current_filename,
                self.codec,
                self.fps,
                (width, height)
            )
            
            if not self.video_writer.isOpened():
                raise Exception("Video writer açılamadı!")
            
            self.is_recording = True
            self.frame_queue = []
            
            # Kayıt thread'ini başlat
            self.recording_thread = threading.Thread(target=self._recording_worker)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            self.recording_started.emit(self.current_filename)
            self.logger.info(f"Video kaydı başlatıldı: {self.current_filename}")
            
            return True
            
        except Exception as e:
            self.recording_error.emit(f"Kayıt başlatma hatası: {str(e)}")
            self.logger.error(f"Kayıt başlatma hatası: {e}")
            return False
    
    def stop_recording(self):
        """Video kaydını durdur"""
        if not self.is_recording:
            return False
        
        self.is_recording = False
        
        # Recording thread'inin bitmesini bekle
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5)
        
        # Video writer'ı kapat
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        filename = self.current_filename
        self.current_filename = None
        
        self.recording_stopped.emit(filename)
        self.logger.info(f"Video kaydı durduruldu: {filename}")
        
        return True
    
    def add_frame(self, frame):
        """Kayıta frame ekle"""
        if self.is_recording:
            # Frame'i kuyruğa ekle
            self.frame_queue.append(frame.copy())
            
            # Kuyruk çok büyürse eski frame'leri at
            if len(self.frame_queue) > 100:
                self.frame_queue.pop(0)
    
    def _recording_worker(self):
        """Kayıt worker thread'i"""
        while self.is_recording:
            try:
                # Frame var mı kontrol et
                if self.frame_queue and self.video_writer:
                    frame = self.frame_queue.pop(0)
                    
                    # Frame'i kaydet
                    self.video_writer.write(frame)
                else:
                    # Bekle
                    time.sleep(0.01)
                    
            except Exception as e:
                self.logger.error(f"Frame yazma hatası: {e}")
                self.recording_error.emit(f"Frame yazma hatası: {str(e)}")
                break
    
    def get_recording_info(self):
        """Kayıt bilgilerini döndür"""
        return {
            'is_recording': self.is_recording,
            'current_filename': self.current_filename,
            'frame_count': len(self.frame_queue) if self.frame_queue else 0,
            'output_dir': self.output_dir
        }
