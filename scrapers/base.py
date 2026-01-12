"""
51.ca 基礎爬蟲類 (整合版)
提供通用的爬蟲功能和日誌系統
"""

import os
import time
import logging
import re
import json
from abc import ABC, abstractmethod
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import Optional, List, Dict, Any

import requests
from bs4 import BeautifulSoup
from opencc import OpenCC

# Handle both direct execution and package import
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .models import (
        init_database, add_url_to_queue, mark_url_visited, 
        get_unvisited_urls, log_scrape, to_json
    )
except ImportError:
    from models import (
        init_database, add_url_to_queue, mark_url_visited, 
        get_unvisited_urls, log_scrape, to_json
    )


# ============== 日誌設置 ==============
def setup_logger(name: str) -> logging.Logger:
    """設置日誌器"""
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d')}_logs.log")
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if logger.handlers:
        return logger
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


class BaseScraper(ABC):
    """基礎爬蟲類"""
    
    SCRAPER_NAME = "base"
    BASE_URL = "https://www.51.ca"
    URL_TYPE = "general"
    
    # HTTP 請求頭
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    def __init__(self, use_browser: bool = False, headless: bool = True):
        self.use_browser = use_browser
        self.headless = headless
        self.logger = setup_logger(self.SCRAPER_NAME)
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        
        # Playwright (可選)
        self.browser = None
        self.page = None
        self.playwright = None
        
        # 統計
        self.stats = {
            'pages_scraped': 0,
            'items_saved': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
        # 簡繁轉換器 (s2twp: 簡體到台灣繁體並轉換用詞)
        self.cc = OpenCC('s2twp')
    
    def start_browser(self):
        """啟動瀏覽器 (需要時才使用)"""
        if not self.use_browser:
            return
            
        try:
            from playwright.sync_api import sync_playwright
            self.logger.info("正在啟動瀏覽器...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            context = self.browser.new_context(
                user_agent=self.DEFAULT_HEADERS['User-Agent'],
                viewport={'width': 1920, 'height': 1080}
            )
            self.page = context.new_page()
            self.logger.info("瀏覽器啟動成功")
        except Exception as e:
            self.logger.warning(f"無法啟動瀏覽器: {e}")
            self.use_browser = False
    
    def close_browser(self):
        """關閉瀏覽器"""
        if self.browser:
            self.browser.close()
            self.browser = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
        self.logger.info("瀏覽器已關閉")
    
    def fetch_page(self, url: str, timeout: int = 10) -> Optional[str]:
        """獲取頁面內容"""
        try:
            if self.use_browser and self.page:
                self.page.goto(url, wait_until='networkidle', timeout=timeout * 1000)
                return self.page.content()
            else:
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                # 優先使用 UTF-8，避免編碼檢測錯誤
                response.encoding = 'utf-8'
                return response.text
        except Exception as e:
            self.logger.error(f"獲取頁面失敗 {url}: {e}")
            return None
    
    def fetch_json(self, url: str, timeout: int = 10) -> Optional[Dict]:
        """獲取JSON數據 (用於API)"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"獲取JSON失敗 {url}: {e}")
            return None
    
    # ============== 工具方法 ==============
    
    def clean_text(self, text: str) -> str:
        """清理文本並轉換為繁體中文"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        # 轉換為繁體中文
        return self.to_traditional(text)
    
    def to_traditional(self, text: str) -> str:
        """將簡體中文轉換為繁體中文"""
        if not text:
            return ""
        try:
            return self.cc.convert(text)
        except:
            return text
    
    @staticmethod
    def extract_text(element) -> str:
        """提取元素文本"""
        if element is None:
            return ""
        return element.get_text(strip=True) if hasattr(element, 'get_text') else str(element)
    
    @staticmethod
    def extract_id_from_url(url: str, pattern: str) -> Optional[str]:
        """從URL中提取ID"""
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    @staticmethod
    def to_json(data) -> Optional[str]:
        """轉換為JSON"""
        return to_json(data)
    
    def decode_cloudflare_email(self, encoded: str) -> str:
        """解碼 Cloudflare 保護的郵箱"""
        try:
            r = int(encoded[:2], 16)
            email = ''.join([chr(int(encoded[i:i+2], 16) ^ r) for i in range(2, len(encoded), 2)])
            return email
        except:
            return ""
    
    # ============== 抽象方法 ==============
    
    @abstractmethod
    def get_start_urls(self) -> List[str]:
        """獲取起始URL列表"""
        pass
    
    @abstractmethod
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面"""
        pass
    
    @abstractmethod
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """解析列表頁面，返回項目列表"""
        pass
    
    @abstractmethod
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """解析詳情頁面，返回項目數據"""
        pass
    
    @abstractmethod
    def save_item(self, data: Dict) -> bool:
        """保存項目到資料庫"""
        pass
    
    # ============== 主要運行方法 ==============
    
    def run(self, start_urls: List[str] = None, max_pages: int = 100):
        """運行爬蟲"""
        self.stats['start_time'] = datetime.now()
        
        self.logger.info("=" * 60)
        self.logger.info(f"開始運行 {self.SCRAPER_NAME} 爬蟲")
        self.logger.info("=" * 60)
        
        # 初始化資料庫
        init_database()
        
        # 啟動瀏覽器 (如果需要)
        if self.use_browser:
            self.start_browser()
        
        try:
            # 添加起始URL到隊列 (列表頁面優先級較低，讓詳情頁面先處理)
            urls = start_urls or self.get_start_urls()
            for url in urls:
                add_url_to_queue(url, self.URL_TYPE, priority=1)
            
            # 處理URL隊列
            while self.stats['pages_scraped'] < max_pages:
                unvisited = get_unvisited_urls(self.URL_TYPE, limit=5)
                if not unvisited:
                    self.logger.info("沒有更多未訪問的URL")
                    break
                
                for url in unvisited:
                    if self.stats['pages_scraped'] >= max_pages:
                        break
                    
                    self.logger.info(f"正在處理: {url}")
                    self._process_url(url)
                    self.stats['pages_scraped'] += 1
                    
                    # 防止請求過快
                    time.sleep(1)
                    
        except Exception as e:
            self.logger.error(f"爬蟲運行錯誤: {e}")
            self.stats['errors'] += 1
        finally:
            if self.use_browser:
                self.close_browser()
        
        self.stats['end_time'] = datetime.now()
        self._print_stats()
    
    def _process_url(self, url: str):
        """處理單個URL"""
        html = self.fetch_page(url)
        if not html:
            mark_url_visited(url, error="Failed to fetch")
            return
        
        try:
            if self.is_list_page(url):
                items = self.parse_list_page(html, url)
                for item in items:
                    if 'url' in item:
                        # 詳情頁面設置較高優先級，確保優先處理
                        add_url_to_queue(item['url'], self.URL_TYPE, source_url=url, priority=5)
            else:
                data = self.parse_detail_page(html, url)
                if data:
                    if self.save_item(data):
                        self.stats['items_saved'] += 1
            
            mark_url_visited(url)
            
        except Exception as e:
            self.logger.error(f"處理頁面錯誤 {url}: {e}")
            mark_url_visited(url, error=str(e))
            self.stats['errors'] += 1
    
    def _print_stats(self):
        """打印統計信息"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        self.logger.info("=" * 60)
        self.logger.info("爬蟲運行統計:")
        self.logger.info(f"  - 頁面爬取: {self.stats['pages_scraped']}")
        self.logger.info(f"  - 項目保存: {self.stats['items_saved']}")
        self.logger.info(f"  - 錯誤數量: {self.stats['errors']}")
        self.logger.info(f"  - 運行時間: {duration:.2f} 秒")
        self.logger.info("=" * 60)