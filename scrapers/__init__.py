"""
51.ca 爬蟲系統 - 整合版
"""

from .models import init_database
from .base import BaseScraper, setup_logger

__all__ = [
    'init_database',
    'BaseScraper', 
    'setup_logger',
]
