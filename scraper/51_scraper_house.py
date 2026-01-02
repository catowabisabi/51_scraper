"""
51.ca 房屋爬蟲
爬取 house.51.ca 的房屋列表 (MLS 買賣 + 租房)
增強版：更好的資料提取和多種 URL 格式支援
"""

import re
import json
import time
from typing import List, Dict, Optional
from datetime import datetime

from bs4 import BeautifulSoup

from base_scraper import BaseScraper
from models import save_house_listing, add_url_to_queue


class HouseScraper(BaseScraper):
    """房屋爬蟲"""
    
    SCRAPER_NAME = "house_scraper"
    BASE_URL = "https://house.51.ca"
    URL_TYPE = "house"
    
    # 房屋類型映射
    PROPERTY_TYPES = {
        '独立屋': '獨立屋', 'detached': '獨立屋',
        '半独立': '半獨立屋', 'semi-detached': '半獨立屋', 'semi': '半獨立屋',
        '镇屋': '鎮屋', 'townhouse': '鎮屋', 'town': '鎮屋', 'freehold townhouse': '鎮屋',
        '公寓': '公寓', 'condo': '公寓', 'apartment': '公寓', 'condo apt': '公寓',
        '联排': '聯排屋', 'row': '聯排屋',
        'stacked townhouse': '疊層鎮屋',
        'multiplex': '多戶住宅',
        'duplex': '雙拼屋',
        'triplex': '三拼屋',
        'fourplex': '四拼屋',
        'link': '連屋',
        'bungalow': '平房',
        '2-storey': '兩層',
        '3-storey': '三層',
    }
    
    # 城市列表 (大多倫多地區)
    CITIES = [
        'Toronto', 'Markham', 'Richmond Hill', 'Vaughan', 'Mississauga',
        'Scarborough', 'North York', 'Etobicoke', 'Brampton', 'Oakville',
        'Burlington', 'Milton', 'Aurora', 'Newmarket', 'Whitby', 'Oshawa',
        'Pickering', 'Ajax', 'Stouffville', 'King City', 'Caledon',
        '多伦多', '万锦', '列治文山', '旺市', '密西沙加', '士嘉堡', '北约克',
        '怡陶碧谷', '宾顿', '奥克维尔', '伯灵顿', '米尔顿', '奥罗拉', '新市',
    ]
    
    def get_start_urls(self) -> List[str]:
        """獲取起始URL列表"""
        urls = [
            # MLS 二手房
            f"{self.BASE_URL}/mls",
            f"{self.BASE_URL}/mls?page=2",
            f"{self.BASE_URL}/mls?page=3",
            # 租房
            f"{self.BASE_URL}/rental",
            f"{self.BASE_URL}/rental?page=2",
            # 不同城市
            f"{self.BASE_URL}/mls?city=toronto",
            f"{self.BASE_URL}/mls?city=markham",
            f"{self.BASE_URL}/mls?city=richmond-hill",
            f"{self.BASE_URL}/mls?city=vaughan",
            f"{self.BASE_URL}/mls?city=mississauga",
        ]
        return urls
    
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面"""
        # 詳情頁格式:
        # - /property/MLS號
        # - /rental/ontario/city/area/id
        # - /mls/ontario/city/area/id (新格式)
        if '/property/' in url:
            return False
        if re.search(r'/rental/ontario/[^/]+/[^/]+/\d+', url):
            return False
        if re.search(r'/mls/ontario/[^/]+/[^/]+/\d+', url):
            return False
        # URL 結尾是數字 ID
        if re.search(r'/\d{5,}$', url):
            return False
        return True
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """解析房屋列表頁面"""
        soup = BeautifulSoup(html, "lxml")
        items = []
        seen_urls = set()
        
        # 1. 查找 /property/MLS 格式的連結
        property_links = soup.find_all('a', href=re.compile(r'/property/[A-Z]\d+'))
        for link in property_links:
            href = link.get('href', '')
            if not href:
                continue
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
        
        # 2. 查找 redirect 格式
        redirect_links = soup.find_all('a', href=re.compile(r'/redirect/property/'))
        for link in redirect_links:
            href = link.get('href', '')
            match = re.search(r'/redirect/property/([A-Z]\d+)', href)
            if match:
                mls_id = match.group(1)
                property_url = f"{self.BASE_URL}/property/{mls_id}"
                if property_url not in seen_urls:
                    seen_urls.add(property_url)
                    items.append({'url': property_url})
        
        # 3. 查找租房詳情頁連結 /rental/ontario/...
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
        
        # 4. 查找所有可能的房源卡片連結 (帶有數字 ID)
        all_links = soup.find_all('a', href=re.compile(r'house\.51\.ca.*\d{5,}'))
        for link in all_links:
            href = link.get('href', '')
            if not href or 'login' in href or 'my/' in href:
                continue
            if href.startswith('http') and 'house.51.ca' in href:
                href = href.split('?')[0]
                if href not in seen_urls:
                    seen_urls.add(href)
                    items.append({'url': href})
        
        self.logger.info(f"列表頁面發現 {len(items)} 個房源")
        return items
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """解析房屋詳情頁面"""
        soup = BeautifulSoup(html, "lxml")
        
        # 檢查是否為 404 頁面
        if '找不到' in html or "can't be found" in html.lower() or 'Oops!' in html:
            self.logger.warning(f"頁面不存在: {url}")
            return None
        
        # 提取 MLS 號碼或租房 ID
        listing_id = self._extract_listing_id(html, url)
        if not listing_id:
            self.logger.warning(f"無法提取房源ID: {url}")
            return None
        
        # 判斷是租房還是買賣
        listing_type = self._extract_listing_type(html, url)
        
        # 提取地址/標題
        title, address = self._extract_title_address(soup, html)
        
        # 提取價格
        price, price_unit = self._extract_price(soup, html, listing_type)
        
        # 提取房屋類型
        property_type = self._extract_property_type(soup, html)
        
        # 提取房間信息
        bedrooms, bathrooms, parking = self._extract_rooms(soup, html)
        
        # 提取面積
        sqft = self._extract_sqft(soup, html)
        
        # 提取城市和社區
        city, community = self._extract_location(soup, html, url, address)
        
        # 提取描述
        description = self._extract_description(soup, html)
        
        # 提取特點
        features = self._extract_features(soup, html)
        
        # 提取經紀人信息
        agent_name, agent_phone, agent_company = self._extract_agent(soup, html)
        
        # 提取圖片
        image_urls = self._extract_images(soup, html)
        
        # 提取設施標籤
        amenities = self._extract_amenities(soup, html)
        
        data = {
            'listing_id': listing_id,
            'url': url,
            'title': title or address or f"房源 {listing_id}",
            'listing_type': listing_type,
            'property_type': property_type,
            'price': price,
            'price_unit': price_unit,
            'address': address,
            'city': city,
            'community': community,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'parking': parking,
            'sqft': sqft,
            'description': description,
            'features': self.to_json(features) if features else None,
            'agent_name': agent_name,
            'agent_phone': agent_phone,
            'agent_company': agent_company,
            'image_urls': self.to_json(image_urls) if image_urls else None,
            'amenities': self.to_json(amenities) if amenities else None
        }
        
        self.logger.info(f"解析房源: {listing_id} - {address or title or 'N/A'}")
        return data
    
    def _extract_listing_id(self, html: str, url: str) -> Optional[str]:
        """提取房源 ID"""
        # 從 URL 提取
        # /property/N12345678
        match = re.search(r'/property/([A-Z]\d+)', url)
        if match:
            return match.group(1)
        
        # /rental/.../604800
        match = re.search(r'/(\d{5,})$', url)
        if match:
            return match.group(1)
        
        # 從頁面內容提取 MLS 號
        mls_patterns = [
            r'MLS[#®\s]*[:：]?\s*([A-Z]\d{7,})',
            r'MLS[#®\s]*[:：]?\s*([A-Z]\d+)',
            r'"mlsNumber"\s*:\s*"([A-Z]\d+)"',
            r'listing.*?([A-Z]\d{7,})',
        ]
        for pattern in mls_patterns:
            match = re.search(pattern, html, re.I)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_listing_type(self, html: str, url: str) -> str:
        """判斷交易類型"""
        text = html.lower()
        if '/rental/' in url or '出租' in html or 'for rent' in text or '/月' in html:
            return '出租'
        return '出售'
    
    def _extract_title_address(self, soup: BeautifulSoup, html: str) -> tuple:
        """提取標題和地址"""
        title = ""
        address = ""
        
        # 嘗試找 h1, h2, h3 標題
        for tag in ['h1', 'h2', 'h3']:
            elem = soup.find(tag)
            if elem:
                text = self.clean_text(self.extract_text(elem))
                # 排除一些無關的標題
                if text and not any(x in text for x in ['找不到', '404', '登录', '注册', '还款明细', '51找房']):
                    title = text
                    break
        
        # 嘗試從 class 包含 address 的元素提取
        addr_elem = soup.find(class_=re.compile(r'address|location|property-address', re.I))
        if addr_elem:
            addr_text = self.clean_text(self.extract_text(addr_elem))
            if addr_text and '登录' not in addr_text:
                address = addr_text
        
        # 如果沒找到地址，嘗試從標題中提取 (地址通常包含街道號碼)
        if not address and title:
            # 檢查標題是否看起來像地址 (包含數字和街道名)
            if re.search(r'\d+\s+\w+', title):
                address = title
        
        # 嘗試從 meta 標籤提取
        if not address:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                content = meta_desc.get('content', '')
                # 嘗試提取地址模式
                addr_match = re.search(r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Way|Court|Ct|Crescent|Cres|Circle|Lane|Ln)[^,]*)', content, re.I)
                if addr_match:
                    address = addr_match.group(1).strip()
        
        # 從頁面 JSON 數據提取
        json_patterns = [
            r'"address"\s*:\s*"([^"]+)"',
            r'"streetAddress"\s*:\s*"([^"]+)"',
            r'"propertyAddress"\s*:\s*"([^"]+)"',
        ]
        if not address:
            for pattern in json_patterns:
                match = re.search(pattern, html)
                if match:
                    address = match.group(1)
                    break
        
        return title, address
    
    def _extract_price(self, soup: BeautifulSoup, html: str, listing_type: str) -> tuple:
        """提取價格"""
        price = None
        price_unit = "CAD"
        
        if listing_type == '出租':
            price_unit = "CAD/月"
        
        # 查找價格元素 (各種可能的 class)
        price_classes = ['price', 'listing-price', 'property-price', 'amount', 'cost']
        for cls in price_classes:
            elem = soup.find(class_=re.compile(cls, re.I))
            if elem:
                text = self.extract_text(elem)
                match = re.search(r'\$\s*([\d,]+)', text)
                if match:
                    try:
                        price = float(match.group(1).replace(',', ''))
                        return price, price_unit
                    except ValueError:
                        pass
        
        # 從整個頁面搜索價格模式
        price_patterns = [
            r'"price"\s*:\s*["\']?\$?\s*([\d,]+)',
            r'"listPrice"\s*:\s*["\']?\$?\s*([\d,]+)',
            r'(?:售價|租金|价格|Price)[：:\s]*\$\s*([\d,]+)',
            r'\$\s*([\d,]{4,})',  # $1,000 以上
        ]
        for pattern in price_patterns:
            match = re.search(pattern, html, re.I)
            if match:
                try:
                    price = float(match.group(1).replace(',', ''))
                    return price, price_unit
                except ValueError:
                    pass
        
        return price, price_unit
    
    def _extract_property_type(self, soup: BeautifulSoup, html: str) -> str:
        """提取房屋類型"""
        text = html.lower()
        
        # 按優先順序檢查
        for keyword, prop_type in self.PROPERTY_TYPES.items():
            if keyword.lower() in text:
                return prop_type
        
        return "其他"
    
    def _extract_rooms(self, soup: BeautifulSoup, html: str) -> tuple:
        """提取房間信息"""
        bedrooms = None
        bathrooms = None
        parking = None
        
        # 臥室模式
        bed_patterns = [
            r'(\d+)\s*\+\s*(\d+)\s*(?:臥|卧|bedroom|bed|房)',  # 3+1 bedroom
            r'(\d+)\s*(?:臥|卧|bedroom|bed|房間|间)',
            r'(?:臥室|卧室|Bedroom|Bed)[：:\s]*(\d+)',
            r'"bedrooms?"\s*:\s*["\']?(\d+)',
            r'(\d+)\s*br\b',
        ]
        for pattern in bed_patterns:
            match = re.search(pattern, html, re.I)
            if match:
                if match.lastindex and match.lastindex >= 2:
                    bedrooms = f"{match.group(1)}+{match.group(2)}"
                else:
                    bedrooms = match.group(1)
                break
        
        # 浴室模式
        bath_patterns = [
            r'(\d+)\s*(?:浴|bathroom|bath|washroom|wr)',
            r'(?:浴室|Bathroom|Bath)[：:\s]*(\d+)',
            r'"bathrooms?"\s*:\s*["\']?(\d+)',
        ]
        for pattern in bath_patterns:
            match = re.search(pattern, html, re.I)
            if match:
                bathrooms = match.group(1)
                break
        
        # 車位模式
        park_patterns = [
            r'(?:車位|车位|Parking|Garage)[：:\s]*(\d+)',
            r'(\d+)\s*(?:車位|车位|parking|garage)',
            r'"parking"\s*:\s*["\']?(\d+)',
        ]
        for pattern in park_patterns:
            match = re.search(pattern, html, re.I)
            if match:
                parking = match.group(1)
                break
        
        return bedrooms, bathrooms, parking
    
    def _extract_sqft(self, soup: BeautifulSoup, html: str) -> str:
        """提取面積"""
        patterns = [
            r'(?:使用面積|面积|Size|Sqft)[：:\s]*([\d,]+)\s*[-–~]\s*([\d,]+)',  # 範圍格式
            r'(?:使用面積|面积|Size|Sqft)[：:\s]*([\d,]+)',
            r'([\d,]+)\s*[-–~]\s*([\d,]+)\s*(?:sqft|sq\.?\s*ft|平方尺)',
            r'([\d,]+)\s*(?:sqft|sq\.?\s*ft|平方尺)',
            r'"squareFeet"\s*:\s*["\']?([\d,]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                if match.lastindex and match.lastindex >= 2:
                    return f"{match.group(1)}-{match.group(2)}"
                return match.group(1)
        return None
    
    def _extract_location(self, soup: BeautifulSoup, html: str, url: str, address: str) -> tuple:
        """提取城市和社區"""
        city = None
        community = None
        
        # 從 URL 提取城市
        # /rental/ontario/toronto/north-york/604800
        url_match = re.search(r'/ontario/([^/]+)/([^/]+)/', url)
        if url_match:
            city = url_match.group(1).replace('-', ' ').title()
            community = url_match.group(2).replace('-', ' ').title()
            return city, community
        
        # 從地址和頁面內容檢測城市
        text = f"{address} {html}"
        for c in self.CITIES:
            if c.lower() in text.lower():
                city = c
                break
        
        # 嘗試提取社區
        community_match = re.search(r'(?:社區|社区|Community|Area|Neighbourhood)[：:\s]*([^\n,<]+)', html)
        if community_match:
            community = self.clean_text(community_match.group(1))[:50]
        
        return city, community
    
    def _extract_description(self, soup: BeautifulSoup, html: str) -> str:
        """提取描述"""
        # 移除不需要的元素
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            tag.decompose()
        
        # 嘗試找描述區域
        desc_selectors = [
            '.description', '.property-description', '.listing-description',
            '.detail-content', '.content', '#description',
            'div[class*="desc"]', 'div[class*="content"]'
        ]
        
        for selector in desc_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(separator='\n', strip=True)
                # 過濾掉太短或無意義的內容
                if len(text) > 50 and '51找房' not in text and '登录' not in text:
                    return self.clean_text(text)[:3000]
        
        # 從 JSON 提取描述
        desc_patterns = [
            r'"description"\s*:\s*"([^"]{50,})"',
            r'"remarks"\s*:\s*"([^"]{50,})"',
            r'"propertyDescription"\s*:\s*"([^"]{50,})"',
        ]
        for pattern in desc_patterns:
            match = re.search(pattern, html)
            if match:
                return self.clean_text(match.group(1))[:3000]
        
        return ""
    
    def _extract_features(self, soup: BeautifulSoup, html: str) -> List[str]:
        """提取房屋特點"""
        features = []
        
        # 常見特點關鍵詞
        feature_keywords = [
            '新裝修', '新装修', '全新', '翻新', 'renovated', 'updated',
            '地下室', 'basement', 'finished basement',
            '車庫', '车库', 'garage', 'attached garage',
            '游泳池', 'pool', 'swimming pool',
            '壁爐', '壁炉', 'fireplace',
            '中央空調', '中央空调', 'central air', 'a/c',
            '硬木地板', 'hardwood', 'hardwood floor',
            '花崗岩', '花岗岩', 'granite',
            '不銹鋼電器', '不锈钢', 'stainless steel',
            '開放式廚房', '开放式厨房', 'open concept',
            '陽台', '阳台', 'balcony',
            '露台', 'deck', 'patio',
            '後院', '后院', 'backyard',
            '近地鐵', '近地铁', 'subway', 'ttc',
            '近學校', '近学校', 'school',
            '安靜', '安静', 'quiet',
            '景觀', '景观', 'view',
        ]
        
        text = html.lower()
        for feature in feature_keywords:
            if feature.lower() in text:
                features.append(feature)
        
        return list(set(features))[:20]
    
    def _extract_agent(self, soup: BeautifulSoup, html: str) -> tuple:
        """提取經紀人信息"""
        agent_name = None
        agent_phone = None
        agent_company = None
        
        # 從 JSON 提取
        json_patterns = [
            (r'"agentName"\s*:\s*"([^"]+)"', 'name'),
            (r'"realtorName"\s*:\s*"([^"]+)"', 'name'),
            (r'"agentPhone"\s*:\s*"([^"]+)"', 'phone'),
            (r'"brokerageName"\s*:\s*"([^"]+)"', 'company'),
        ]
        for pattern, field in json_patterns:
            match = re.search(pattern, html)
            if match:
                if field == 'name' and not agent_name:
                    agent_name = match.group(1)
                elif field == 'phone' and not agent_phone:
                    agent_phone = match.group(1)
                elif field == 'company' and not agent_company:
                    agent_company = match.group(1)
        
        # 查找經紀人區塊
        if not agent_name:
            agent_elem = soup.find(class_=re.compile(r'agent|realtor|broker|contact', re.I))
            if agent_elem:
                agent_text = self.extract_text(agent_elem)
                # 排除無關內容
                if agent_text and '是否' not in agent_text and '登录' not in agent_text and len(agent_text) < 100:
                    agent_name = self.clean_text(agent_text)
        
        # 提取電話
        if not agent_phone:
            phone_patterns = [
                r'(?:電話|电话|Tel|Phone)[：:\s]*(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
                r'\b(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})\b',
            ]
            for pattern in phone_patterns:
                match = re.search(pattern, html)
                if match:
                    agent_phone = match.group(1)
                    break
        
        # 提取公司
        if not agent_company:
            company_patterns = [
                r'(?:經紀公司|经纪公司|Brokerage|Company)[：:\s]*([^\n<]+)',
                r'(Re/Max[^\n<]*)',
                r'(Royal LePage[^\n<]*)',
                r'(Century 21[^\n<]*)',
                r'(Sutton[^\n<]*)',
                r'(Homelife[^\n<]*)',
                r'(iPro[^\n<]*)',
            ]
            for pattern in company_patterns:
                match = re.search(pattern, html, re.I)
                if match:
                    agent_company = self.clean_text(match.group(1))[:100]
                    break
        
        return agent_name, agent_phone, agent_company
    
    def _extract_images(self, soup: BeautifulSoup, html: str) -> List[str]:
        """提取圖片 URL"""
        images = []
        seen = set()
        
        # 排除關鍵詞
        exclude_keywords = ['logo', 'icon', 'avatar', 'button', 'banner', 'ad', 
                          'googlemap', 'map.svg', 'loading', 'placeholder', 
                          'common/images', 'sprite', 'favicon']
        
        # 從 img 標籤提取
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if not src:
                continue
            
            # 排除無關圖片
            if any(x in src.lower() for x in exclude_keywords):
                continue
            
            # 確保是完整 URL
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = f"{self.BASE_URL}{src}"
            
            if src.startswith('http') and src not in seen:
                seen.add(src)
                images.append(src)
        
        # 從 JSON 數據或背景圖片提取
        img_patterns = [
            r'"(?:image|photo|img|pic|photo)(?:Url|Src|s)?"\s*:\s*"([^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
            r'"(?:image|photo|img|pic)(?:Url|Src|s)?"\s*:\s*\[([^\]]+)\]',
            r'background-image:\s*url\(["\']?([^"\')\s]+)["\']?\)',
        ]
        for pattern in img_patterns:
            for match in re.finditer(pattern, html, re.I):
                src = match.group(1)
                # 處理 JSON 數組
                if ',' in src and '"' in src:
                    urls = re.findall(r'"([^"]+)"', src)
                    for url in urls:
                        if url.startswith('//'):
                            url = 'https:' + url
                        elif url.startswith('/'):
                            url = f"{self.BASE_URL}{url}"
                        if url.startswith('http') and url not in seen:
                            seen.add(url)
                            images.append(url)
                else:
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = f"{self.BASE_URL}{src}"
                    if src.startswith('http') and src not in seen:
                        seen.add(src)
                        images.append(src)
        
        return images[:30]  # 最多 30 張
    
    def _extract_amenities(self, soup: BeautifulSoup, html: str) -> List[str]:
        """提取周邊設施"""
        amenities = []
        
        # 周邊設施關鍵詞
        amenity_keywords = [
            ('華人超市', ['华人超市', '大统华', 't&t', 'foody mart', '丰泰', '惠康']),
            ('Costco', ['costco']),
            ('地鐵站', ['地铁', '地鐵', 'subway', 'ttc']),
            ('Go Train', ['go train', 'go station', 'gotrain']),
            ('學校', ['学校', '學校', 'school']),
            ('公園', ['公园', '公園', 'park']),
            ('醫院', ['医院', '醫院', 'hospital']),
            ('購物中心', ['购物中心', '商场', 'mall', 'shopping']),
        ]
        
        text = html.lower()
        for amenity_name, keywords in amenity_keywords:
            for keyword in keywords:
                if keyword.lower() in text:
                    amenities.append(amenity_name)
                    break
        
        return list(set(amenities))
    
    def save_item(self, data: Dict) -> bool:
        """保存房屋列表"""
        return save_house_listing(data)
    
    def run_house_scraper(self, max_pages: int = 50):
        """運行房屋爬蟲"""
        start_urls = self.get_start_urls()
        self.run(start_urls=start_urls, max_pages=max_pages)


def main():
    """主函數"""
    scraper = HouseScraper(headless=True)
    scraper.run_house_scraper(max_pages=30)


if __name__ == "__main__":
    main()
