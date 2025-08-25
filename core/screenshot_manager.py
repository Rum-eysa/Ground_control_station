# Screenshot Manager
# core/screenshot_manager.py - Ekran görüntüsü yöneticisi
# =============================================================================

import cv2
import os
import numpy as np
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
import logging

class ScreenshotManager(QObject):
    screenshot_saved = pyqtSignal(str)  # filename
    screenshot_error = pyqtSignal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self.output_dir = "data/screenshots"
        self.logger = logging.getLogger(__name__)
        
        # Dizin oluştur
        os.makedirs(self.output_dir, exist_ok=True)
    
    def save_screenshot(self, frame, filename=None):
        """Ekran görüntüsü kaydet"""
        try:
            # Dosya adı oluştur
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Millisecond precision
                filename = f"screenshot_{timestamp}.png"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # Frame'i kaydet
            success = cv2.imwrite(filepath, frame)
            
            if success:
                self.screenshot_saved.emit(filepath)
                self.logger.info(f"Ekran görüntüsü kaydedildi: {filepath}")
                return filepath
            else:
                raise Exception("Dosya yazılamadı!")
                
        except Exception as e:
            error_msg = f"Ekran görüntüsü kaydetme hatası: {str(e)}"
            self.screenshot_error.emit(error_msg)
            self.logger.error(error_msg)
            return None
    
    def save_annotated_screenshot(self, frame, annotations, filename=None):
        """Açıklamalı ekran görüntüsü kaydet"""
        try:
            # Frame kopyası oluştur
            annotated_frame = frame.copy()
            
            # Açıklamaları ekle
            for annotation in annotations:
                self._add_annotation(annotated_frame, annotation)
            
            # Timestamp ekle
            self._add_timestamp(annotated_frame)
            
            return self.save_screenshot(annotated_frame, filename)
            
        except Exception as e:
            error_msg = f"Açıklamalı ekran görüntüsü hatası: {str(e)}"
            self.screenshot_error.emit(error_msg)
            self.logger.error(error_msg)
            return None
    
    def _add_annotation(self, frame, annotation):
        """Frame'e açıklama ekle"""
        annotation_type = annotation.get('type', 'text')
        
        if annotation_type == 'text':
            self._add_text(frame, annotation)
        elif annotation_type == 'rectangle':
            self._add_rectangle(frame, annotation)
        elif annotation_type == 'circle':
            self._add_circle(frame, annotation)
        elif annotation_type == 'arrow':
            self._add_arrow(frame, annotation)
    
    def _add_text(self, frame, annotation):
        """Metin açıklaması ekle"""
        text = annotation.get('text', '')
        position = annotation.get('position', (50, 50))
        font_scale = annotation.get('font_scale', 1.0)
        color = annotation.get('color', (0, 255, 0))
        thickness = annotation.get('thickness', 2)
        
        cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX,
                   font_scale, color, thickness)
    
    def _add_rectangle(self, frame, annotation):
        """Dikdörtgen açıklaması ekle"""
        start_point = annotation.get('start_point', (0, 0))
        end_point = annotation.get('end_point', (100, 100))
        color = annotation.get('color', (0, 255, 0))
        thickness = annotation.get('thickness', 2)
        
        cv2.rectangle(frame, start_point, end_point, color, thickness)
    
    def _add_circle(self, frame, annotation):
        """Daire açıklaması ekle"""
        center = annotation.get('center', (50, 50))
        radius = annotation.get('radius', 20)
        color = annotation.get('color', (0, 255, 0))
        thickness = annotation.get('thickness', 2)
        
        cv2.circle(frame, center, radius, color, thickness)
    
    def _add_arrow(self, frame, annotation):
        """Ok açıklaması ekle"""
        start_point = annotation.get('start_point', (0, 0))
        end_point = annotation.get('end_point', (50, 50))
        color = annotation.get('color', (0, 255, 0))
        thickness = annotation.get('thickness', 2)
        
        # Ok çiz
        cv2.arrowedLine(frame, start_point, end_point, color, thickness)
    
    def _add_timestamp(self, frame):
        """Zaman damgası ekle"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Alt sağ köşeye ekle
        height, width = frame.shape[:2]
        position = (width - 200, height - 20)
        
        # Arka plan dikdörtgeni
        cv2.rectangle(frame, (width - 210, height - 35), 
                     (width - 5, height - 5), (0, 0, 0), -1)
        
        # Zaman damgası metni
        cv2.putText(frame, timestamp, position, cv2.FONT_HERSHEY_SIMPLEX,
                   0.5, (255, 255, 255), 1)
