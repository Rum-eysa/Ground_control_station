# Logger
# core/logger.py - Gelişmiş log sistemi
# =============================================================================

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from PyQt5.QtCore import QObject, pyqtSignal

class LogHandler(logging.Handler, QObject):
    """Qt sinyali destekleyen log handler"""
    log_message = pyqtSignal(str, str)  # level, message
    
    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
    
    def emit(self, record):
        msg = self.format(record)
        self.log_message.emit(record.levelname, msg)

def setup_logging(log_level="INFO", log_dir="data/logs"):
    """Logging sistemini ayarla"""
    # Log dizinini oluştur
    os.makedirs(log_dir, exist_ok=True)
    
    # Ana logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    console_formatter = logging.Formatter(
        '%(levelname)s - %(name)s - %(message)s'
    )
    
    # File handler (rotating)
    log_file = os.path.join(log_dir, f"ground_control_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Error file handler
    error_file = os.path.join(log_dir, f"errors_{datetime.now().strftime('%Y%m%d')}.log")
    error_handler = RotatingFileHandler(
        error_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # Handler'ları ekle
    logger.addHandler(file_handler)
    logger.addHandler(console_handler) 
    logger.addHandler(error_handler)
    
    # İlk log mesajı
    logger.info("Ground Control Station logging sistemi başlatıldı")
    
    return logger
