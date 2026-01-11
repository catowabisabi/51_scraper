"""
51.ca 新聞爬蟲 (整合版)
爬取 info.51.ca 的新聞文章
使用 Playwright 來獲取動態內容
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
        'local': '本地',
        'chinese': '華人',
    }
    
    # 排除關鍵詞 (不應出現在正文中)
    EXCLUDE_KEYWORDS = [
        '本地要闻', '生活资讯', '中国和国际', '查看更多文章', '往期头条',
        '网友评论', '请先', '点击登录', '推荐房源', '生活服务',
        '广告报价', 'APP下载', '投资理财', '商家动态', '如何展示在这里',
        '二手汽车', '查看全部房源', '关于我们', '法律声明', '隐私政策',
        '加国无忧旗下站点', '帮助中心', '编辑邮箱', '网友评论仅供其表达个人看法',
        '51.CA 立场', '51首页', '点击查看繁體版', '加国无忧APP下载',
    ]
    
    def __init__(self, use_browser: bool = True, headless: bool = True):
        """初始化爬蟲，預設使用瀏覽器"""
        super().__init__(use_browser=use_browser, headless=headless)
    
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
            
            # 跳過評論頁面
            if '/comments' in href:
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
        title = self._extract_title(soup)
        
        # 分類
        category = self._extract_category(soup, url)
        
        # 發布時間
        publish_date = self._extract_publish_date(soup)
        
        # 作者/來源
        author, source = self._extract_author_source(soup)
        
        # 正文 (改進版)
        content = self._extract_content(soup)
        
        # 摘要
        summary = content[:200] + "..." if len(content) > 200 else content
        
        # 圖片
        image_urls = self._extract_images(soup)
        
        # 評論數
        comment_count = self._extract_comment_count(soup)
        
        # 標籤
        tags = self._extract_tags(soup)
        
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
            'tags': self.to_json(tags) if tags else None
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取標題"""
        # 首先找 h1
        h1 = soup.find('h1')
        if h1:
            title = self.clean_text(h1.get_text())
            if title and len(title) > 5:
                return title
        
        # 找 title 標籤
        title_tag = soup.find('title')
        if title_tag:
            title = self.clean_text(title_tag.get_text())
            # 移除網站名稱後綴
            title = re.sub(r'\s*[-|]\s*(51\.CA|加国无忧).*$', '', title)
            return title
        
        return ""
    
    def _extract_category(self, soup: BeautifulSoup, url: str) -> str:
        """提取分類"""
        # 從URL提取
        for key, value in self.CATEGORIES.items():
            if f'/{key}' in url:
                return value
        
        # 從頁面元素提取
        text = soup.get_text()
        for key, value in self.CATEGORIES.items():
            if value in text[:500]:  # 只在頁面前部查找
                return value
        
        return '綜合'
    
    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """提取發布時間"""
        text = soup.get_text()
        
        # 格式: 發布：2026年01月10日 18:29
        match = re.search(r'發布[：:]\s*(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{2})', text)
        if match:
            return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)} {match.group(4).zfill(2)}:{match.group(5)}:00"
        
        # 格式: 发布：2026年01月10日 18:29 (简体)
        match = re.search(r'发布[：:]\s*(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{2})', text)
        if match:
            return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)} {match.group(4).zfill(2)}:{match.group(5)}:00"
        
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
        
        # 絕對時間 YYYY-MM-DD
        match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取正文內容 (改進版)"""
        # 移除不需要的元素
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
            tag.decompose()
        
        # 移除評論區域
        for elem in soup.find_all(class_=re.compile(r'comment|footer|sidebar|recommend|related')):
            elem.decompose()
        
        content_parts = []
        
        # 方法1: 查找文章主體區域
        article_selectors = [
            'article',
            '.article-content',
            '.article-body',
            '.post-content',
            '.news-content',
            '.arc-body',
            '.arcbody',
            '[class*="article"]',
        ]
        
        article_elem = None
        for selector in article_selectors:
            article_elem = soup.select_one(selector)
            if article_elem:
                break
        
        if article_elem:
            # 從文章區域提取段落
            paragraphs = article_elem.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if self._is_valid_paragraph(text):
                    content_parts.append(text)
        
        # 方法2: 如果沒有找到足夠內容，從整個頁面提取
        if len('\n\n'.join(content_parts)) < 100:
            content_parts = []
            all_paragraphs = soup.find_all('p')
            for p in all_paragraphs:
                text = p.get_text(strip=True)
                if self._is_valid_paragraph(text):
                    content_parts.append(text)
        
        # 方法3: 如果還是沒有內容，嘗試提取純文本
        if not content_parts:
            # 找到 h1 標題後的內容
            h1 = soup.find('h1')
            if h1:
                # 獲取 h1 後面的兄弟元素
                for sibling in h1.find_next_siblings():
                    if sibling.name in ['p', 'div']:
                        text = sibling.get_text(strip=True)
                        if self._is_valid_paragraph(text):
                            content_parts.append(text)
                    # 遇到評論區或推薦區停止
                    if sibling.get('class') and any('comment' in c or 'recommend' in c for c in sibling.get('class', [])):
                        break
        
        content = '\n\n'.join(content_parts)
        return self.clean_text(content)
    
    def _is_valid_paragraph(self, text: str) -> bool:
        """檢查段落是否有效"""
        if not text or len(text) < 15:
            return False
        
        # 排除包含無關關鍵詞的段落
        for keyword in self.EXCLUDE_KEYWORDS:
            if keyword in text:
                return False
        
        # 排除只有連結的段落
        if text.startswith('http') or text.startswith('www.'):
            return False
        
        # 排除評論格式的內容
        if re.match(r'^\w+\d+[小时分钟天]前', text):
            return False
        
        return True
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """提取圖片"""
        images = []
        
        # 查找文章中的圖片
        article = soup.find('article') or soup.find(class_=re.compile(r'article|content'))
        search_area = article if article else soup
        
        for img in search_area.find_all('img'):
            src = img.get('data-src') or img.get('src')
            if not src:
                continue
            
            # 排除logo、icon等
            if any(x in src.lower() for x in ['logo', 'icon', 'avatar', 'button', 'banner']):
                continue
            
            # 排除 data URI
            if src.startswith('data:'):
                continue
            
            # 補全 URL
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = self.BASE_URL + src
            
            images.append(src)
        
        return images[:10]
    
    def _extract_author_source(self, soup: BeautifulSoup) -> tuple:
        """提取作者和來源"""
        author = None
        source = None
        text = soup.get_text()
        
        # 查找來源: 來源：加国无忧 51.CA
        match = re.search(r'[來来]源[：:]\s*([^\n]+)', text)
        if match:
            source = match.group(1).strip()
        
        # 查找作者: 作者：51.CA 坚果儿
        match = re.search(r'作者[：:]\s*([^\n]+)', text)
        if match:
            author = match.group(1).strip()
        
        return author, source
    
    def _extract_comment_count(self, soup: BeautifulSoup) -> int:
        """提取評論數"""
        text = soup.get_text()
        match = re.search(r'(\d+)\s*(?:條評論|条评论|評論|评论|comments)', text, re.I)
        if match:
            return int(match.group(1))
        return 0
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """提取標籤"""
        tags = []
        
        # 查找標籤連結
        tag_links = soup.find_all('a', href=re.compile(r'/keywords/'))
        for link in tag_links:
            tag = link.get_text(strip=True)
            if tag and tag not in tags:
                tags.append(tag)
        
        return tags
    
    def save_item(self, data: Dict) -> bool:
        """保存新聞到資料庫"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # 轉換為繁體中文
            title = self.to_traditional(data.get('title', ''))
            summary = self.to_traditional(data.get('summary', ''))
            content = self.to_traditional(data.get('content', ''))
            author = self.to_traditional(data.get('author', '')) if data.get('author') else None
            source = self.to_traditional(data.get('source', '')) if data.get('source') else None
            
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
                author,
                source,
                data['publish_date'],
                data['comment_count'],
                data['view_count'],
                data['image_urls'],
                data['tags']
            ))
            
            conn.commit()
            conn.close()
            self.logger.info(f"保存新聞: {title[:30]}... (內容長度: {len(content)})")
            return True
        except Exception as e:
            self.logger.error(f"保存新聞失敗: {e}")
            return False


if __name__ == "__main__":
    scraper = NewsScraper(use_browser=True, headless=True)
    scraper.run(max_pages=30)
