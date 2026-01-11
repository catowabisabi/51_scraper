"""
51.ca 新聞爬蟲 (整合版)
爬取 info.51.ca 的新聞文章
"""

import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from .base import BaseScraper
from .models import get_connection


class NewsScraper(BaseScraper):
    """新聞爬蟲"""
    
    SCRAPER_NAME = "news"
    BASE_URL = "https://info.51.ca"
    URL_TYPE = "news"
    
    # 新聞分類
    CATEGORIES = {
        'canada': '加國',
        'world': '國際', 
        'china': '中國',
        'entertainment': '體娛',
        'shopping': '購物',
        'travel': '玩樂',
        'real-estate': '房產',
        'money': '理財',
        'deals': '打折',
    }
    
    def get_start_urls(self) -> List[str]:
        """獲取起始URL列表"""
        return [
            f"{self.BASE_URL}/",
            f"{self.BASE_URL}/canada",
            f"{self.BASE_URL}/world",
            f"{self.BASE_URL}/china",
        ]
    
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面"""
        return '/articles/' not in url
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """解析新聞列表頁面"""
        soup = BeautifulSoup(html, "lxml")
        items = []
        
        # 文章URL格式: /articles/1500533
        article_links = soup.find_all('a', href=re.compile(r'/articles/\d+'))
        
        seen_urls = set()
        for link in article_links:
            href = link.get('href', '')
            if not href:
                continue
            
            if href.startswith('/'):
                article_url = f"{self.BASE_URL}{href}"
            elif href.startswith('http'):
                article_url = href
            else:
                continue
            
            article_url = article_url.split('?')[0]
            
            if article_url in seen_urls:
                continue
            seen_urls.add(article_url)
            
            items.append({'url': article_url})
        
        self.logger.info(f"列表頁面發現 {len(items)} 篇文章")
        return items
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """解析新聞詳情頁面"""
        soup = BeautifulSoup(html, "lxml")
        
        article_id = self.extract_id_from_url(url, r'/articles/(\d+)')
        if not article_id:
            return None
        
        # 標題
        title_elem = soup.find('h1') or soup.find('title')
        title = self.clean_text(self.extract_text(title_elem))
        
        # 分類
        category = self._extract_category(soup, url)
        
        # 發布時間
        publish_date = self._extract_publish_date(soup)
        
        # 正文
        content = self._extract_content(soup)
        
        # 摘要
        summary = content[:200] + "..." if len(content) > 200 else content
        
        # 圖片
        image_urls = self._extract_images(soup)
        
        # 作者/來源
        author, source = self._extract_author_source(soup)
        
        # 評論數
        comment_count = self._extract_comment_count(soup)
        
        return {
            'article_id': article_id,
            'url': url,
            'title': title,
            'summary': summary,
            'content': content,
            'category': category,
            'author': author,
            'source': source,
            'publish_date': publish_date,
            'comment_count': comment_count,
            'view_count': 0,
            'image_urls': self.to_json(image_urls),
            'tags': None
        }
    
    def _extract_category(self, soup: BeautifulSoup, url: str) -> str:
        """提取分類"""
        for key, value in self.CATEGORIES.items():
            if f'/{key}' in url:
                return value
        return '綜合'
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """提取發布時間"""
        text = soup.get_text()
        
        # 相對時間
        match = re.search(r'(\d+)小時前', text)
        if match:
            hours = int(match.group(1))
            return (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
        
        match = re.search(r'(\d+)分鐘前', text)
        if match:
            minutes = int(match.group(1))
            return (datetime.now() - timedelta(minutes=minutes)).strftime('%Y-%m-%d %H:%M:%S')
        
        match = re.search(r'(\d+)天前', text)
        if match:
            days = int(match.group(1))
            return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        
        # 絕對時間
        match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        if match:
            return match.group(1)
        
        match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', text)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文"""
        # 主要內容區域
        article_body = soup.find('div', class_=re.compile(r'article[-_]?body|content|arcbody'))
        if article_body:
            # 移除腳本和樣式
            for tag in article_body.find_all(['script', 'style', 'iframe']):
                tag.decompose()
            return self.clean_text(article_body.get_text())
        return ""
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """提取圖片"""
        images = []
        article_body = soup.find('div', class_=re.compile(r'article[-_]?body|content|arcbody'))
        if article_body:
            for img in article_body.find_all('img'):
                src = img.get('data-src') or img.get('src')
                if src and not src.startswith('data:'):
                    images.append(src)
        return images[:10]
    
    def _extract_author_source(self, soup: BeautifulSoup) -> tuple:
        """提取作者和來源"""
        author = None
        source = None
        
        # 查找來源
        source_elem = soup.find(class_=re.compile(r'source'))
        if source_elem:
            text = source_elem.get_text()
            match = re.search(r'來源[:：]\s*(\S+)', text)
            if match:
                source = match.group(1)
        
        return author, source
    
    def _extract_comment_count(self, soup: BeautifulSoup) -> int:
        """提取評論數"""
        text = soup.get_text()
        match = re.search(r'(\d+)\s*(?:條評論|評論|comments)', text, re.I)
        if match:
            return int(match.group(1))
        return 0
    
    def save_item(self, data: Dict) -> bool:
        """保存新聞到資料庫"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # 轉換為繁體中文
            title = self.to_traditional(data.get('title', ''))
            summary = self.to_traditional(data.get('summary', ''))
            content = self.to_traditional(data.get('content', ''))
            
            cursor.execute("""
                INSERT OR REPLACE INTO news_articles (
                    article_id, url, title, summary, content, category,
                    author, source, publish_date, comment_count, view_count,
                    image_urls, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['article_id'],
                data['url'],
                title,
                summary,
                content,
                data['category'],
                data['author'],
                data['source'],
                data['publish_date'],
                data['comment_count'],
                data['view_count'],
                data['image_urls'],
                data['tags']
            ))
            
            conn.commit()
            conn.close()
            self.logger.info(f"保存新聞: {data['title'][:30]}...")
            return True
        except Exception as e:
            self.logger.error(f"保存新聞失敗: {e}")
            return False


if __name__ == "__main__":
    scraper = NewsScraper()
    scraper.run(max_pages=20)
