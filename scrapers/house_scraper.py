"""
51.ca 房屋爬蟲 (整合版)
爬取 house.51.ca 的 MLS 買賣 + 租房信息
"""

import re
from typing import List, Dict, Optional
from datetime import datetime

from bs4 import BeautifulSoup

from .base import BaseScraper
from .models import get_connection


class HouseScraper(BaseScraper):
    """房屋爬蟲"""
    
    SCRAPER_NAME = "house"
    BASE_URL = "https://house.51.ca"
    URL_TYPE = "house"
    
    # 房屋類型映射
    PROPERTY_TYPES = {
        '独立屋': '獨立屋', 'detached': '獨立屋',
        '半独立': '半獨立屋', 'semi-detached': '半獨立屋',
        '镇屋': '鎮屋', 'townhouse': '鎮屋', 'town': '鎮屋',
        '公寓': '公寓', 'condo': '公寓', 'apartment': '公寓',
        '联排': '聯排屋', 'row': '聯排屋',
        'bungalow': '平房',
        'duplex': '雙拼屋',
    }
    
    # 大多倫多地區城市
    CITIES = [
        'Toronto', 'Markham', 'Richmond Hill', 'Vaughan', 'Mississauga',
        'Scarborough', 'North York', 'Etobicoke', 'Brampton', 'Oakville',
    ]
    
    def get_start_urls(self) -> List[str]:
        """獲取起始URL列表"""
        return [
            f"{self.BASE_URL}/mls",
            f"{self.BASE_URL}/mls?page=2",
            f"{self.BASE_URL}/rental",
            f"{self.BASE_URL}/mls?city=toronto",
            f"{self.BASE_URL}/mls?city=markham",
        ]
    
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面"""
        # 詳情頁: /property/MLS號 或 /rental/ontario/.../id
        if '/property/' in url:
            return False
        if re.search(r'/rental/ontario/[^/]+/[^/]+/\d+', url):
            return False
        if re.search(r'/mls/ontario/[^/]+/[^/]+/\d+', url):
            return False
        return True
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """解析房屋列表頁面"""
        soup = BeautifulSoup(html, "lxml")
        items = []
        seen_urls = set()
        
        # 1. /property/MLS 格式
        property_links = soup.find_all('a', href=re.compile(r'/property/[A-Z]\d+'))
        for link in property_links:
            href = link.get('href', '')
            if href.startswith('/'):
                property_url = f"{self.BASE_URL}{href}"
            elif href.startswith('http'):
                property_url = href
            else:
                continue
            property_url = property_url.split('?')[0]
            if property_url not in seen_urls:
                seen_urls.add(property_url)
                items.append({'url': property_url})
        
        # 2. redirect 格式
        redirect_links = soup.find_all('a', href=re.compile(r'/redirect/property/'))
        for link in redirect_links:
            match = re.search(r'/redirect/property/([A-Z]\d+)', link.get('href', ''))
            if match:
                mls_id = match.group(1)
                property_url = f"{self.BASE_URL}/property/{mls_id}"
                if property_url not in seen_urls:
                    seen_urls.add(property_url)
                    items.append({'url': property_url})
        
        # 3. 租房連結
        rental_links = soup.find_all('a', href=re.compile(r'/rental/ontario/[^/]+/[^/]+/\d+'))
        for link in rental_links:
            href = link.get('href', '')
            if href.startswith('/'):
                rental_url = f"{self.BASE_URL}{href}"
            elif href.startswith('http'):
                rental_url = href
            else:
                continue
            rental_url = rental_url.split('?')[0]
            if rental_url not in seen_urls:
                seen_urls.add(rental_url)
                items.append({'url': rental_url})
        
        # 4. feed-list class 中的連結 (來自 HOUSING的主頁.txt)
        feed_list = soup.find(class_='feed-list')
        if feed_list:
            for link in feed_list.find_all('a', href=True):
                href = link.get('href', '')
                if 'house.51.ca' in href or href.startswith('/'):
                    if href.startswith('/'):
                        href = f"{self.BASE_URL}{href}"
                    href = href.split('?')[0]
                    if href not in seen_urls and re.search(r'\d{5,}', href):
                        seen_urls.add(href)
                        items.append({'url': href})
        
        self.logger.info(f"列表頁面發現 {len(items)} 個房源")
        return items
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """解析房屋詳情頁面"""
        soup = BeautifulSoup(html, "lxml")
        
        # 檢查404
        if '找不到' in html or "can't be found" in html.lower():
            return None
        
        listing_id = self._extract_listing_id(html, url)
        if not listing_id:
            return None
        
        listing_type = self._extract_listing_type(html, url)
        title, address = self._extract_title_address(soup)
        price, price_unit = self._extract_price(soup, listing_type)
        property_type = self._extract_property_type(soup)
        bedrooms, bathrooms, parking = self._extract_rooms(soup)
        sqft = self._extract_sqft(soup)
        city, community = self._extract_location(soup, url, address)
        description = self._extract_description(soup)
        features = self._extract_features(soup)
        agent_name, agent_phone, agent_company = self._extract_agent(soup)
        image_urls = self._extract_images(soup)
        
        return {
            'listing_id': listing_id,
            'url': url,
            'title': title,
            'listing_type': listing_type,
            'property_type': property_type,
            'address': address,
            'city': city,
            'community': community,
            'price': price,
            'price_unit': price_unit,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'parking': parking,
            'sqft': sqft,
            'description': description,
            'features': self.to_json(features),
            'agent_name': agent_name,
            'agent_phone': agent_phone,
            'agent_company': agent_company,
            'image_urls': self.to_json(image_urls),
        }
    
    def _extract_listing_id(self, html: str, url: str) -> Optional[str]:
        """提取房源ID"""
        # MLS格式
        match = re.search(r'/property/([A-Z]\d+)', url)
        if match:
            return match.group(1)
        
        # 租房格式
        match = re.search(r'/(\d+)$', url)
        if match:
            return match.group(1)
        
        # 從HTML提取
        match = re.search(r'MLS[#®]?\s*([A-Z]\d+)', html, re.I)
        if match:
            return match.group(1)
        
        return None
    
    def _extract_listing_type(self, html: str, url: str) -> str:
        """提取房源類型"""
        if '/rental' in url or '出租' in html or 'rental' in html.lower():
            return '出租'
        return '出售'
    
    def _extract_title_address(self, soup: BeautifulSoup) -> tuple:
        """提取標題和地址"""
        title = ""
        address = ""
        
        # 標題
        title_elem = soup.find('h1')
        if title_elem:
            title = self.clean_text(title_elem.get_text())
        
        # 地址
        address_elem = soup.find(class_=re.compile(r'address|location'))
        if address_elem:
            address = self.clean_text(address_elem.get_text())
        
        # 如果沒有單獨地址，用標題
        if not address:
            address = title
        
        return title, address
    
    def _extract_price(self, soup: BeautifulSoup, listing_type: str) -> tuple:
        """提取價格"""
        price = None
        price_unit = None
        
        price_elem = soup.find(class_=re.compile(r'price'))
        if price_elem:
            text = price_elem.get_text()
            match = re.search(r'\$?([\d,]+)', text)
            if match:
                price = float(match.group(1).replace(',', ''))
        
        if listing_type == '出租':
            price_unit = '月'
        
        return price, price_unit
    
    def _extract_property_type(self, soup: BeautifulSoup) -> str:
        """提取房屋類型"""
        text = soup.get_text().lower()
        
        for key, value in self.PROPERTY_TYPES.items():
            if key in text:
                return value
        
        return None
    
    def _extract_rooms(self, soup: BeautifulSoup) -> tuple:
        """提取房間信息"""
        text = soup.get_text()
        
        # 臥室
        bedrooms = None
        match = re.search(r'(\d+)\s*(?:bedroom|bed|臥室|房)', text, re.I)
        if match:
            bedrooms = int(match.group(1))
        
        # 浴室
        bathrooms = None
        match = re.search(r'(\d+)\s*(?:bathroom|bath|浴室|廁)', text, re.I)
        if match:
            bathrooms = int(match.group(1))
        
        # 車位
        parking = None
        match = re.search(r'(\d+)\s*(?:parking|garage|車位|車庫)', text, re.I)
        if match:
            parking = int(match.group(1))
        
        return bedrooms, bathrooms, parking
    
    def _extract_sqft(self, soup: BeautifulSoup) -> Optional[int]:
        """提取面積"""
        text = soup.get_text()
        match = re.search(r'([\d,]+)\s*(?:sq\s*ft|sqft|平方呎)', text, re.I)
        if match:
            return int(match.group(1).replace(',', ''))
        return None
    
    def _extract_location(self, soup: BeautifulSoup, url: str, address: str) -> tuple:
        """提取城市和社區"""
        city = None
        community = None
        
        # 從URL提取
        for c in self.CITIES:
            if c.lower() in url.lower() or c.lower() in address.lower():
                city = c
                break
        
        return city, community
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """提取描述"""
        desc_elem = soup.find(class_=re.compile(r'description|content'))
        if desc_elem:
            return self.clean_text(desc_elem.get_text())[:2000]
        return ""
    
    def _extract_features(self, soup: BeautifulSoup) -> List[str]:
        """提取特點"""
        features = []
        feature_elem = soup.find(class_=re.compile(r'feature|amenity'))
        if feature_elem:
            for li in feature_elem.find_all('li'):
                features.append(self.clean_text(li.get_text()))
        return features[:20]
    
    def _extract_agent(self, soup: BeautifulSoup) -> tuple:
        """提取經紀人信息"""
        agent_name = None
        agent_phone = None
        agent_company = None
        
        agent_elem = soup.find(class_=re.compile(r'agent|realtor|broker'))
        if agent_elem:
            # 名字
            name_elem = agent_elem.find(class_=re.compile(r'name'))
            if name_elem:
                agent_name = self.clean_text(name_elem.get_text())
            
            # 電話
            phone_elem = agent_elem.find(class_=re.compile(r'phone|tel'))
            if phone_elem:
                agent_phone = self.clean_text(phone_elem.get_text())
        
        return agent_name, agent_phone, agent_company
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """提取圖片"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('data-src') or img.get('src')
            if src and ('51img' in src or 'storage' in src) and 'logo' not in src:
                images.append(src)
        return list(set(images))[:20]
    
    def save_item(self, data: Dict) -> bool:
        """保存房屋到資料庫"""
        try:
            # 繁體中文轉換
            title = self.to_traditional(data['title'])
            address = self.to_traditional(data['address'])
            description = self.to_traditional(data['description'])
            features = self.to_traditional(data['features'])
            agent_name = self.to_traditional(data['agent_name'])
            
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO house_listings (
                    listing_id, url, title, listing_type, property_type,
                    address, city, community, price, price_unit,
                    bedrooms, bathrooms, parking, sqft, description,
                    features, agent_name, agent_phone, agent_company, image_urls
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['listing_id'],
                data['url'],
                title,
                data['listing_type'],
                data['property_type'],
                address,
                data['city'],
                data['community'],
                data['price'],
                data['price_unit'],
                data['bedrooms'],
                data['bathrooms'],
                data['parking'],
                data['sqft'],
                description,
                features,
                agent_name,
                data['agent_phone'],
                data['agent_company'],
                data['image_urls']
            ))
            
            conn.commit()
            conn.close()
            self.logger.info(f"保存房源: {title[:30]}...")
            return True
        except Exception as e:
            self.logger.error(f"保存房屋失敗: {e}")
            return False


if __name__ == "__main__":
    scraper = HouseScraper()
    scraper.run(max_pages=20)
