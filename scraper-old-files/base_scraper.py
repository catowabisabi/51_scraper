"""
51.ca 基礎爬蟲類
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

from playwright.sync_api import sync_playwright, Page, Browser
from bs4 import BeautifulSoup

from models import (
    init_database, add_url_to_queue, mark_url_visited, 
    get_unvisited_urls, log_scrape
)


# ============== 日誌設置 ==============
def setup_logger(name: str) -> logging.Logger:
    """設置日誌器"""
    # 創建 logs 目錄
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # 日誌文件名: 日期_logs.log
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d')}_logs.log")
    
    # 創建 logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 避免重複添加 handler
    if logger.handlers:
        return logger
    
    # 文件 handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 控制台 handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 格式
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
    
    # 子類需要定義這些屬性
    SCRAPER_NAME = "base"
    BASE_URL = "https://www.51.ca"
    URL_TYPE = "general"
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.logger = setup_logger(self.SCRAPER_NAME)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        # 統計
        self.stats = {
            'pages_scraped': 0,
            'items_saved': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def start_browser(self):
        """啟動瀏覽器"""
        self.logger.info("正在啟動瀏覽器...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = context.new_page()
        self.logger.info("瀏覽器啟動成功")
    
    def close_browser(self):
        """關閉瀏覽器"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.logger.info("瀏覽器已關閉")
    
    def fetch_page(self, url: str, wait_time: float = 2.0) -> Optional[str]:
        """獲取頁面HTML"""
        try:
            self.logger.debug(f"正在訪問: {url}")
            self.page.goto(url, timeout=30000, wait_until="domcontentloaded")
            time.sleep(wait_time)
            html = self.page.content()
            self.stats['pages_scraped'] += 1
            return html
        except Exception as e:
            self.logger.error(f"獲取頁面失敗 {url}: {e}")
            self.stats['errors'] += 1
            return None
    
    def extract_links(self, html: str, base_url: str, pattern: str = None) -> List[str]:
        """從HTML中提取連結"""
        soup = BeautifulSoup(html, "lxml")
        links = set()
        
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(base_url, href)
            
            # 清理URL
            parsed = urlparse(full_url)
            if parsed.scheme not in ("http", "https"):
                continue
            
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                clean_url += f"?{parsed.query}"
            
            # 如果有pattern，進行過濾
            if pattern and not re.search(pattern, clean_url):
                continue
            
            # 確保是51.ca的URL
            if "51.ca" in parsed.netloc:
                links.add(clean_url)
        
        return list(links)
    
    def extract_text(self, element, default: str = "") -> str:
        """安全提取文字"""
        if element:
            return element.get_text(strip=True)
        return default
    
    def extract_attr(self, element, attr: str, default: str = "") -> str:
        """安全提取屬性"""
        if element and element.has_attr(attr):
            return element[attr]
        return default
    
    def clean_text(self, text: str) -> str:
        """清理文字"""
        if not text:
            return ""
        # 移除多餘空白
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_id_from_url(self, url: str, pattern: str) -> Optional[str]:
        """從URL提取ID"""
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None
    
    def to_json(self, data: Any) -> str:
        """轉換為JSON字符串"""
        if isinstance(data, (list, dict)):
            return json.dumps(data, ensure_ascii=False)
        return str(data) if data else ""
    
    @abstractmethod
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """解析列表頁面，返回項目列表 - 子類必須實現"""
        pass
    
    @abstractmethod
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """解析詳情頁面，返回項目數據 - 子類必須實現"""
        pass
    
    @abstractmethod
    def save_item(self, data: Dict) -> bool:
        """保存項目到資料庫 - 子類必須實現"""
        pass
    
    def scrape_list_page(self, url: str) -> int:
        """爬取列表頁面"""
        start_time = time.time()
        
        html = self.fetch_page(url)
        if not html:
            log_scrape(self.SCRAPER_NAME, url, "failed", 0, "無法獲取頁面", 0)
            mark_url_visited(url, False, "無法獲取頁面")
            return 0
        
        items = self.parse_list_page(html, url)
        
        # 將詳情頁URL添加到隊列
        for item in items:
            if 'url' in item:
                add_url_to_queue(item['url'], self.URL_TYPE, url, priority=1)
        
        duration = time.time() - start_time
        log_scrape(self.SCRAPER_NAME, url, "success", len(items), None, duration)
        mark_url_visited(url, True)
        
        self.logger.info(f"列表頁面爬取完成: {url}, 發現 {len(items)} 個項目")
        return len(items)
    
    def scrape_detail_page(self, url: str) -> bool:
        """爬取詳情頁面"""
        start_time = time.time()
        
        html = self.fetch_page(url)
        if not html:
            log_scrape(self.SCRAPER_NAME, url, "failed", 0, "無法獲取頁面", 0)
            mark_url_visited(url, False, "無法獲取頁面")
            return False
        
        data = self.parse_detail_page(html, url)
        if not data:
            log_scrape(self.SCRAPER_NAME, url, "failed", 0, "解析失敗", 0)
            mark_url_visited(url, False, "解析失敗")
            return False
        
        success = self.save_item(data)
        if success:
            self.stats['items_saved'] += 1
        
        duration = time.time() - start_time
        status = "success" if success else "failed"
        log_scrape(self.SCRAPER_NAME, url, status, 1 if success else 0, None, duration)
        mark_url_visited(url, success)
        
        return success
    
    def run(self, start_urls: List[str] = None, max_pages: int = 100):
        """運行爬蟲"""
        self.logger.info(f"=" * 60)
        self.logger.info(f"開始運行 {self.SCRAPER_NAME} 爬蟲")
        self.logger.info(f"=" * 60)
        
        self.stats['start_time'] = datetime.now()
        
        # 初始化資料庫
        init_database()
        
        # 啟動瀏覽器
        self.start_browser()
        
        try:
            # 添加起始URL
            if start_urls:
                for url in start_urls:
                    add_url_to_queue(url, self.URL_TYPE, None, priority=10)
            
            pages_processed = 0
            
            while pages_processed < max_pages:
                # 獲取未訪問的URL
                urls = get_unvisited_urls(self.URL_TYPE, limit=5)
                
                if not urls:
                    self.logger.info("沒有更多未訪問的URL")
                    break
                
                for url in urls:
                    if pages_processed >= max_pages:
                        break
                    
                    self.logger.info(f"正在處理: {url}")
                    
                    # 根據URL類型決定處理方式
                    if self.is_list_page(url):
                        self.scrape_list_page(url)
                    else:
                        self.scrape_detail_page(url)
                    
                    pages_processed += 1
                    time.sleep(1)  # 避免請求過快
            
        except KeyboardInterrupt:
            self.logger.info("用戶中斷爬蟲")
        except Exception as e:
            self.logger.error(f"爬蟲運行錯誤: {e}")
        finally:
            self.close_browser()
        
        self.stats['end_time'] = datetime.now()
        self.print_stats()
    
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面 - 子類可以覆寫"""
        return False
    
    def print_stats(self):
        """打印統計信息"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        self.logger.info(f"=" * 60)
        self.logger.info(f"爬蟲運行統計:")
        self.logger.info(f"  - 頁面爬取: {self.stats['pages_scraped']}")
        self.logger.info(f"  - 項目保存: {self.stats['items_saved']}")
        self.logger.info(f"  - 錯誤數量: {self.stats['errors']}")
        self.logger.info(f"  - 運行時間: {duration:.2f} 秒")
        self.logger.info(f"=" * 60)


if __name__ == "__main__":
    # 測試日誌
    logger = setup_logger("test")
    logger.info("日誌系統測試成功！")
    
    # 初始化資料庫
    init_database()
