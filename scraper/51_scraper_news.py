"""
51.ca 新聞爬蟲
爬取 info.51.ca 的新聞文章
"""

import re
import json
from typing import List, Dict, Optional
from datetime import datetime

from bs4 import BeautifulSoup

from base_scraper import BaseScraper
from models import save_news_article, add_url_to_queue


class NewsScraper(BaseScraper):
    """新聞爬蟲"""
    
    SCRAPER_NAME = "news_scraper"
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
        urls = [
            f"{self.BASE_URL}/",  # 首頁
            f"{self.BASE_URL}/canada",  # 加國新聞
            f"{self.BASE_URL}/world",   # 國際新聞
        ]
        return urls
    
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面"""
        # 列表頁面通常不包含 /articles/
        return '/articles/' not in url
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """解析新聞列表頁面"""
        soup = BeautifulSoup(html, "lxml")
        items = []
        
        # 查找所有文章連結
        # 文章URL格式: https://info.51.ca/articles/1500533
        article_links = soup.find_all('a', href=re.compile(r'/articles/\d+'))
        
        seen_urls = set()
        for link in article_links:
            href = link.get('href', '')
            if not href:
                continue
            
            # 構建完整URL
            if href.startswith('/'):
                article_url = f"{self.BASE_URL}{href}"
            elif href.startswith('http'):
                article_url = href
            else:
                continue
            
            # 清理URL (移除查詢參數)
            article_url = article_url.split('?')[0]
            
            # 避免重複
            if article_url in seen_urls:
                continue
            seen_urls.add(article_url)
            
            # 提取標題
            title = self.extract_text(link)
            
            items.append({
                'url': article_url,
                'title': title
            })
        
        self.logger.info(f"列表頁面發現 {len(items)} 篇文章")
        return items
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """解析新聞詳情頁面"""
        soup = BeautifulSoup(html, "lxml")
        
        # 提取文章ID
        article_id = self.extract_id_from_url(url, r'/articles/(\d+)')
        if not article_id:
            self.logger.warning(f"無法提取文章ID: {url}")
            return None
        
        # 提取標題
        title_elem = soup.find('h1') or soup.find('title')
        title = self.clean_text(self.extract_text(title_elem))
        
        # 提取分類
        category = self._extract_category(soup, url)
        
        # 提取發布時間
        publish_date = self._extract_publish_date(soup)
        
        # 提取評論數
        comment_count = self._extract_comment_count(soup)
        
        # 提取正文內容
        content = self._extract_content(soup)
        
        # 提取摘要 (取正文前200字)
        summary = content[:200] + "..." if len(content) > 200 else content
        
        # 提取圖片
        image_urls = self._extract_images(soup)
        
        # 提取作者/來源
        author, source = self._extract_author_source(soup)
        
        data = {
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
        
        self.logger.debug(f"解析文章: {title[:30]}...")
        return data
    
    def _extract_category(self, soup: BeautifulSoup, url: str) -> str:
        """提取文章分類"""
        # 從URL提取
        for key, value in self.CATEGORIES.items():
            if f'/{key}' in url:
                return value
        
        # 從頁面元素提取
        category_elem = soup.find('span', class_=re.compile(r'category|tag'))
        if category_elem:
            return self.extract_text(category_elem)
        
        return '綜合'
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """提取發布時間"""
        # 查找時間元素
        time_patterns = [
            r'(\d+)小時前',
            r'(\d+)分鐘前',
            r'(\d+)天前',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
        ]
        
        # 查找包含時間的元素
        text = soup.get_text()
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                time_str = match.group(0)
                
                # 轉換相對時間為絕對時間
                if '小時前' in time_str:
                    hours = int(match.group(1))
                    from datetime import timedelta
                    return (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
                elif '分鐘前' in time_str:
                    minutes = int(match.group(1))
                    from datetime import timedelta
                    return (datetime.now() - timedelta(minutes=minutes)).strftime('%Y-%m-%d %H:%M:%S')
                elif '天前' in time_str:
                    days = int(match.group(1))
                    from datetime import timedelta
                    return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    return time_str
        
        return None
    
    def _extract_comment_count(self, soup: BeautifulSoup) -> int:
        """提取評論數"""
        # 查找評論數元素
        comment_elem = soup.find(string=re.compile(r'\d+\s*評論'))
        if comment_elem:
            match = re.search(r'(\d+)', comment_elem)
            if match:
                return int(match.group(1))
        return 0
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取文章正文"""
        # 移除不需要的元素
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            tag.decompose()
        
        # 查找文章內容區域
        content_selectors = [
            'article',
            '.article-content',
            '.article-body',
            '.content',
            '.post-content',
            'main',
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                text = content_elem.get_text(separator='\n', strip=True)
                if len(text) > 100:  # 確保有足夠內容
                    return self.clean_text(text)
        
        # 如果找不到特定區域，取body內容
        body = soup.find('body')
        if body:
            return self.clean_text(body.get_text(separator='\n', strip=True))
        
        return ""
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """提取圖片URL"""
        images = []
        
        # 查找文章中的圖片
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and not any(x in src for x in ['logo', 'icon', 'avatar', 'button']):
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = self.BASE_URL + src
                images.append(src)
        
        return images[:10]  # 最多保存10張圖片
    
    def _extract_author_source(self, soup: BeautifulSoup) -> tuple:
        """提取作者和來源"""
        author = None
        source = None
        
        # 查找作者
        author_elem = soup.find(class_=re.compile(r'author'))
        if author_elem:
            author = self.extract_text(author_elem)
        
        # 查找來源
        source_elem = soup.find(string=re.compile(r'來源[：:]\s*'))
        if source_elem:
            match = re.search(r'來源[：:]\s*(.+)', source_elem)
            if match:
                source = match.group(1).strip()
        
        return author, source
    
    def save_item(self, data: Dict) -> bool:
        """保存新聞文章"""
        return save_news_article(data)
    
    def run_news_scraper(self, max_pages: int = 50):
        """運行新聞爬蟲"""
        start_urls = self.get_start_urls()
        self.run(start_urls=start_urls, max_pages=max_pages)


def main():
    """主函數"""
    scraper = NewsScraper(headless=True)
    scraper.run_news_scraper(max_pages=30)


if __name__ == "__main__":
    main()
