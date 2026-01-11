"""
51.ca 活動爬蟲 (整合版)
爬取 www.51.ca 的社區活動信息

CSS Selectors 來源: 
- data_structures_人類defined/活動詳情頁面結構.txt
- data_structures_人類defined/活動頁面的活動的locat方法.txt
"""

import re
from typing import List, Dict, Optional
from datetime import datetime

from bs4 import BeautifulSoup

from .base import BaseScraper
from .models import get_connection


class EventScraper(BaseScraper):
    """活動爬蟲"""
    
    SCRAPER_NAME = "event"
    BASE_URL = "https://www.51.ca"
    URL_TYPE = "event"
    
    # 活動分類
    CATEGORIES = [
        'events',        # 社區活動
        'promotions',    # 商家優惠
    ]
    
    def get_start_urls(self) -> List[str]:
        """獲取起始URL列表"""
        return [
            f"{self.BASE_URL}/events",
            f"{self.BASE_URL}/events?page=2",
            f"{self.BASE_URL}/promotions",
        ]
    
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面"""
        # 詳情頁: /events/數字 或 /event/數字
        if re.search(r'/events?/\d+$', url):
            return False
        return True
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """
        解析活動列表頁面
        使用: li.wg51__feeds-item.event 選擇器
        """
        soup = BeautifulSoup(html, "lxml")
        items = []
        seen_urls = set()
        
        # 方法1: li.wg51__feeds-item.event (活動頁面的活動的locat方法.txt)
        event_items = soup.select('li.wg51__feeds-item.event')
        for item in event_items:
            link = item.find('a', href=True)
            if link:
                href = link.get('href', '')
                if href.startswith('/'):
                    event_url = f"{self.BASE_URL}{href}"
                elif href.startswith('http'):
                    event_url = href
                else:
                    continue
                
                event_url = event_url.split('?')[0]
                if event_url not in seen_urls:
                    seen_urls.add(event_url)
                    
                    # 提取 data-id
                    event_id = link.get('data-id') or self.extract_id_from_url(event_url, r'/(\d+)$')
                    items.append({
                        'url': event_url,
                        'event_id': event_id,
                    })
        
        # 方法2: li.wg51__feeds-item.stream-mixed-large (推廣/廣告)
        promo_items = soup.select('li.wg51__feeds-item.stream-mixed-large')
        for item in promo_items:
            link = item.find('a', href=True)
            if link:
                href = link.get('href', '')
                if '/events' in href or '/event' in href:
                    if href.startswith('/'):
                        event_url = f"{self.BASE_URL}{href}"
                    elif href.startswith('http'):
                        event_url = href
                    else:
                        continue
                    
                    event_url = event_url.split('?')[0]
                    if event_url not in seen_urls:
                        seen_urls.add(event_url)
                        items.append({'url': event_url})
        
        # 方法3: 通用連結搜索
        event_links = soup.find_all('a', href=re.compile(r'/events?/\d+'))
        for link in event_links:
            href = link.get('href', '')
            if href.startswith('/'):
                event_url = f"{self.BASE_URL}{href}"
            elif href.startswith('http'):
                event_url = href
            else:
                continue
            
            event_url = event_url.split('?')[0]
            if event_url not in seen_urls:
                seen_urls.add(event_url)
                items.append({'url': event_url})
        
        self.logger.info(f"列表頁面發現 {len(items)} 個活動")
        return items
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """
        解析活動詳情頁面
        CSS Selectors 來自 活動詳情頁面結構.txt
        """
        soup = BeautifulSoup(html, "lxml")
        
        event_id = self.extract_id_from_url(url, r'/(\d+)$')
        if not event_id:
            return None
        
        # 標題: #article-main h1
        title = ""
        title_elem = soup.select_one('#article-main h1')
        if title_elem:
            title = self.clean_text(title_elem.get_text())
        
        # 發佈時間: #article-main .article-meta .source span:nth-of-type(1)
        published_at = None
        pub_elem = soup.select_one('#article-main .article-meta .source span')
        if pub_elem:
            published_at = self.clean_text(pub_elem.get_text())
        
        # 來源: #article-main .article-meta .source span:nth-of-type(2)
        source = None
        source_elems = soup.select('#article-main .article-meta .source span')
        if len(source_elems) > 1:
            source = self.clean_text(source_elems[1].get_text())
        
        # 活動卡片: .events-card
        card = soup.select_one('.events-card')
        
        # 活動時間
        start_time = None
        end_time = None
        if card:
            # 查找 dt + dd 配對
            dts = card.find_all('dt')
            for dt in dts:
                dt_text = dt.get_text().strip()
                dd = dt.find_next_sibling('dd')
                if dd:
                    dd_text = self.clean_text(dd.get_text())
                    
                    if '开始时间' in dt_text or '活動時間' in dt_text:
                        start_time = dd_text
                    elif '结束时间' in dt_text:
                        end_time = dd_text
        
        # 地區: dt:contains("所在地区") + dd
        region = self._extract_dd_value(card, '所在地区')
        
        # 聯絡人: dt:contains("联系人") + dd
        contact_person = self._extract_dd_value(card, '联系人')
        
        # 電話: .events-card a.phone
        phone = None
        if card:
            phone_elem = card.select_one('a.phone')
            if phone_elem:
                phone = self.clean_text(phone_elem.get_text())
        
        # 電郵 (Cloudflare 保護): .events-card a.email span.__cf_email__
        email = None
        if card:
            email_elem = card.select_one('span.__cf_email__')
            if email_elem:
                encoded = email_elem.get('data-cfemail', '')
                if encoded:
                    email = self.decode_cloudflare_email(encoded)
        
        # 地址: dt:contains("相关地址") + dd
        address = self._extract_dd_value(card, '相关地址')
        
        # 正文 HTML: #arcbody
        content = ""
        content_elem = soup.select_one('#arcbody')
        if content_elem:
            # 移除腳本
            for tag in content_elem.find_all(['script', 'style']):
                tag.decompose()
            content = self.clean_text(content_elem.get_text())
        
        # 正文圖片: #arcbody img.detail-lazy-image [data-src]
        images = []
        if content_elem:
            for img in content_elem.select('img.detail-lazy-image'):
                src = img.get('data-src') or img.get('data-srcset') or img.get('src')
                if src and not src.startswith('data:'):
                    images.append(src)
        
        # 判斷類型
        event_type = '活動'
        if '/promotions' in url or '優惠' in title or '打折' in title:
            event_type = '優惠'
        
        return {
            'event_id': event_id,
            'url': url,
            'title': title,
            'event_type': event_type,
            'start_time': start_time,
            'end_time': end_time,
            'location': region,
            'address': address,
            'contact_person': contact_person,
            'contact_phone': phone,
            'contact_email': email,
            'description': content[:2000],
            'source': source,
            'published_at': published_at,
            'image_urls': self.to_json(images[:10]),
        }
    
    def _extract_dd_value(self, card, dt_contains: str) -> Optional[str]:
        """從 dt + dd 配對中提取值"""
        if not card:
            return None
        
        dts = card.find_all('dt')
        for dt in dts:
            if dt_contains in dt.get_text():
                dd = dt.find_next_sibling('dd')
                if dd:
                    return self.clean_text(dd.get_text())
        return None
    
    def save_item(self, data: Dict) -> bool:
        """保存活動到資料庫（匹配 models.py 的 events 架構）"""
        try:
            # 繁體中文轉換
            title = self.to_traditional(data.get('title'))
            description = self.to_traditional(data.get('description'))
            location = self.to_traditional(data.get('location'))
            address = self.to_traditional(data.get('address'))
            contact_person = self.to_traditional(data.get('contact_person'))
            source = self.to_traditional(data.get('source'))
            
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO events (
                    event_id, url, title, event_type,
                    start_time, end_time, location, region, address,
                    contact_person, contact_phone, contact_email,
                    content, content_images, source, published_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('event_id'),
                data.get('url'),
                title,
                data.get('event_type'),
                data.get('start_time'),
                data.get('end_time'),
                location,
                location,  # region = location
                address,
                contact_person,
                data.get('contact_phone'),
                data.get('contact_email'),
                description,
                data.get('image_urls'),  # content_images
                source,
                data.get('published_at'),
            ))
            
            conn.commit()
            conn.close()
            self.logger.info(f"保存活動: {title[:30] if title else 'N/A'}...")
            return True
        except Exception as e:
            self.logger.error(f"保存活動失敗: {e}")
            return False


if __name__ == "__main__":
    scraper = EventScraper()
    scraper.run(max_pages=20)
