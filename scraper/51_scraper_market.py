"""
51.ca 集市爬蟲
爬取 www.51.ca/market 的二手交易信息
"""

import re
import json
from typing import List, Dict, Optional
from datetime import datetime

from bs4 import BeautifulSoup

from base_scraper import BaseScraper
from models import get_connection, add_url_to_queue


class MarketScraper(BaseScraper):
    """集市爬蟲"""
    
    SCRAPER_NAME = "market_scraper"
    BASE_URL = "https://www.51.ca/market"
    URL_TYPE = "market"
    
    # 集市分類 (新URL結構)
    MARKET_CATEGORIES = {
        'all': '全部',
        'furniture': '家具',
        'home-appliance': '生活家电',
        'kitchen-supplies': '厨房用品',
        'mother-baby-products': '母婴用品',
        'auto-parts': '汽车配件',
        'gardening': '花草园艺',
        'electronic-products': '电子产品',
        'computer-phone': '电脑手机',
        'jewelry': '珠宝首饰',
        'digital-equipment': '数码设备',
        'sports-leisure': '运动休闲',
        'musical-instruments': '乐器音响',
        'pet-supplies': '宠物用品',
        'other': '其他物品',
    }
    
    def get_start_urls(self) -> List[str]:
        """獲取起始URL列表"""
        urls = [
            f"{self.BASE_URL}/all",
            f"{self.BASE_URL}/furniture",
            f"{self.BASE_URL}/home-appliance",
            f"{self.BASE_URL}/kitchen-supplies",
            f"{self.BASE_URL}/electronic-products",
        ]
        return urls
    
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面"""
        # 詳情頁格式: /market/post/數字ID
        if re.search(r'/market/post/\d+', url):
            return False
        return True
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """解析集市列表頁面"""
        soup = BeautifulSoup(html, "lxml")
        items = []
        
        # 查找帖子連結 - 多種可能的URL格式
        patterns = [
            r'/market/post/\d+',
            r'/market/\d+',
            r'/market/[^/]+/\d+',
        ]
        
        seen_urls = set()
        for pattern in patterns:
            post_links = soup.find_all('a', href=re.compile(pattern))
            for link in post_links:
                href = link.get('href', '')
                if not href or '/my/' in href or 'login' in href:
                    continue
                
                if href.startswith('/'):
                    post_url = f"https://www.51.ca{href}"
                elif href.startswith('http'):
                    post_url = href
                else:
                    continue
                
                post_url = post_url.split('?')[0]
                
                if post_url in seen_urls:
                    continue
                seen_urls.add(post_url)
                
                items.append({'url': post_url})
        
        self.logger.info(f"列表頁面發現 {len(items)} 個集市帖子")
        return items
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """解析集市詳情頁面"""
        soup = BeautifulSoup(html, "lxml")
        
        post_id = self.extract_id_from_url(url, r'/post/(\d+)')
        if not post_id:
            return None
        
        # 提取帖子信息
        title = self._extract_title(soup)
        category = self._extract_category(url)
        price = self._extract_price(soup)
        original_price = self._extract_original_price(soup)
        condition = self._extract_condition(soup)
        description = self._extract_description(soup)
        location = self._extract_location(soup)
        contact_info = self._extract_contact(soup)
        image_urls = self._extract_images(soup)
        post_date = self._extract_post_date(soup)
        view_count = self._extract_view_count(soup)
        
        return {
            'post_id': post_id,
            'url': url,
            'title': title,
            'category': category,
            'price': price,
            'original_price': original_price,
            'condition': condition,
            'description': description,
            'location': location,
            'contact_info': contact_info,
            'image_urls': self.to_json(image_urls),
            'post_date': post_date,
            'view_count': view_count,
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取標題"""
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            title = self.clean_text(self.extract_text(title_elem))
            title = re.sub(r'\s*[-|].*51\.ca.*$', '', title)
            return title
        return ""
    
    def _extract_category(self, url: str) -> str:
        """提取分類"""
        for cat_key, cat_name in self.MARKET_CATEGORIES.items():
            if cat_key in url:
                return cat_name
        return None
    
    def _extract_price(self, soup: BeautifulSoup) -> float:
        """提取價格"""
        price_elem = soup.find(class_=re.compile(r'price|amount'))
        if price_elem:
            text = self.extract_text(price_elem)
            match = re.search(r'\$?\s*([\d,.]+)', text)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    pass
        return None
    
    def _extract_original_price(self, soup: BeautifulSoup) -> float:
        """提取原價"""
        orig_elem = soup.find(class_=re.compile(r'original|old-price|was'))
        if orig_elem:
            text = self.extract_text(orig_elem)
            match = re.search(r'\$?\s*([\d,.]+)', text)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except ValueError:
                    pass
        return None
    
    def _extract_condition(self, soup: BeautifulSoup) -> str:
        """提取物品狀態"""
        text = soup.get_text()
        conditions = {
            '全新': '全新',
            '九成新': '九成新',
            '八成新': '八成新',
            '七成新': '七成新',
            '二手': '二手',
            '新品': '全新',
            'new': '全新',
            'used': '二手',
            'like new': '九成新',
        }
        text_lower = text.lower()
        for key, value in conditions.items():
            if key.lower() in text_lower:
                return value
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """提取描述"""
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        
        desc_elem = soup.find(class_=re.compile(r'description|content|detail|body'))
        if desc_elem:
            return self.clean_text(desc_elem.get_text(separator='\n', strip=True))[:2000]
        return ""
    
    def _extract_location(self, soup: BeautifulSoup) -> str:
        """提取位置"""
        loc_elem = soup.find(class_=re.compile(r'location|area|region'))
        if loc_elem:
            return self.clean_text(self.extract_text(loc_elem))
        
        # 從文本中查找常見地區名
        text = soup.get_text()
        locations = ['士嘉堡', '北约克', '万锦', '列治文山', '密西沙加', 
                     '多伦多市中心', '大多地区', '旺市', '宾顿', '奥克维尔',
                     'Scarborough', 'North York', 'Markham', 'Richmond Hill', 
                     'Mississauga', 'Toronto', 'Vaughan', 'Brampton', 'Oakville']
        for loc in locations:
            if loc in text:
                return loc
        return None
    
    def _extract_contact(self, soup: BeautifulSoup) -> str:
        """提取聯繫方式"""
        contacts = []
        
        # 電話
        text = soup.get_text()
        phone_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', text)
        if phone_match:
            contacts.append(f"電話: {phone_match.group(1)}")
        
        # 微信
        wechat_match = re.search(r'微信[号號]?\s*[：:]\s*(\S+)', text)
        if wechat_match:
            contacts.append(f"微信: {wechat_match.group(1)}")
        
        # 郵箱
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            contacts.append(f"郵箱: {email_match.group(0)}")
        
        return '; '.join(contacts) if contacts else None
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """提取圖片"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and not any(x in src.lower() for x in ['logo', 'icon', 'avatar', 'button', 'ad']):
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://www.51.ca' + src
                if src.startswith('http'):
                    images.append(src)
        return images[:15]
    
    def _extract_post_date(self, soup: BeautifulSoup) -> str:
        """提取發布日期"""
        date_elem = soup.find(class_=re.compile(r'date|time|posted'))
        if date_elem:
            text = self.extract_text(date_elem)
            # 嘗試解析日期
            date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', text)
            if date_match:
                return date_match.group(1)
        return None
    
    def _extract_view_count(self, soup: BeautifulSoup) -> int:
        """提取瀏覽次數"""
        view_elem = soup.find(string=re.compile(r'瀏覽|浏览|views?', re.I))
        if view_elem:
            text = str(view_elem)
            match = re.search(r'(\d+)', text)
            if match:
                return int(match.group(1))
        return 0
    
    def save_item(self, data: Dict) -> bool:
        """保存集市帖子"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO market_posts 
                (post_id, url, title, category, price, original_price,
                 condition, description, location, contact_info, image_urls,
                 post_date, view_count, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('post_id'),
                data.get('url'),
                data.get('title'),
                data.get('category'),
                data.get('price'),
                data.get('original_price'),
                data.get('condition'),
                data.get('description'),
                data.get('location'),
                data.get('contact_info'),
                data.get('image_urls'),
                data.get('post_date'),
                data.get('view_count', 0),
                datetime.now()
            ))
            conn.commit()
            self.logger.info(f"保存集市帖子: {data.get('title', 'N/A')}")
            return True
        except Exception as e:
            self.logger.error(f"保存集市帖子失敗: {e}")
            return False
        finally:
            conn.close()
    
    def run_market_scraper(self, max_pages: int = 50):
        """運行集市爬蟲"""
        start_urls = self.get_start_urls()
        self.run(start_urls=start_urls, max_pages=max_pages)


def main():
    """主函數"""
    scraper = MarketScraper(headless=True)
    scraper.run_market_scraper(max_pages=30)


if __name__ == "__main__":
    main()
