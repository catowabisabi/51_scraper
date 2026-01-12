"""
51.ca 汽車爬蟲 (整合版)
爬取 auto.51.ca 的二手車、新車、轉lease信息

Schema 來源: data_structures_人類defined/二手車項目頁頁schema.json
包含: promotions (當日批核, 零信用OK, 無工作OK, 送車上門, 保修)
"""

import re
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import sys
import os

from bs4 import BeautifulSoup

# Add the parent directory of 'scrapers' to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base import BaseScraper
from models import get_connection


class AutoScraper(BaseScraper):
    """汽車爬蟲"""
    
    SCRAPER_NAME = "auto"
    BASE_URL = "https://www.51.ca/autos"
    URL_TYPE = "auto"
    
    # 汽車品牌
    CAR_BRANDS = [
        'Toyota', 'Honda', 'Nissan', 'Mazda', 'BMW', 'Mercedes', 'Audi',
        'Lexus', 'Acura', 'Infiniti', 'Ford', 'Chevrolet', 'Hyundai',
        'Kia', 'Volkswagen', 'Subaru', 'Tesla', 'Porsche', 'Jeep',
        'GMC', 'Ram', 'Dodge', 'Chrysler', 'Buick', 'Cadillac',
        'Land Rover', 'Jaguar', 'Volvo', 'Mini', 'Fiat', 'Mitsubishi',
    ]
    
    # Promotion 標籤映射
    PROMOTION_LABELS = {
        '当日批核': 'same_day_approval',
        '当天批核': 'same_day_approval',
        '零信用ok': 'no_credit_ok',
        '无信用ok': 'no_credit_ok',
        '无工作ok': 'no_job_ok',
        '没工作ok': 'no_job_ok',
        '送车上门': 'delivery_available',
        '送車上門': 'delivery_available',
        '原厂保修': 'warranty_available',
        '原廠保修': 'warranty_available',
        '保修': 'warranty_available',
    }
    
    def get_start_urls(self) -> List[str]:
        """獲取起始URL列表"""
        return [
            f"{self.BASE_URL}/",
            f"{self.BASE_URL}/used-cars",
            f"{self.BASE_URL}/new-cars",
            f"{self.BASE_URL}/lease-cars",
            f"{self.BASE_URL}/used-cars?page=2",
            f"{self.BASE_URL}/used-cars?page=3",
        ]
    
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面"""
        # 詳情頁: /autos/used-cars/數字
        if re.search(r'/autos/(used-cars|new-cars|lease-cars)/\d+$', url):
            return False
        return True
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """解析汽車列表頁面"""
        soup = BeautifulSoup(html, "lxml")
        items = []
        seen_urls = set()
        
        # 查找汽車連結
        car_links = soup.find_all('a', href=re.compile(r'/autos/(used-cars|new-cars|lease-cars)/\d+'))
        
        for link in car_links:
            href = link.get('href', '')
            if not href or '/my/' in href:
                continue
            
            if href.startswith('/'):
                car_url = f"https://www.51.ca{href}"
            elif href.startswith('http'):
                car_url = href
            else:
                continue
            
            car_url = car_url.split('?')[0]
            
            if car_url in seen_urls:
                continue
            seen_urls.add(car_url)
            
            items.append({'url': car_url})
        
        self.logger.info(f"列表頁面發現 {len(items)} 輛車")
        return items
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """
        解析汽車詳情頁面
        基於 二手車項目頁頁schema.json
        優先從 __NEXT_DATA__ JSON 提取數據
        """
        soup = BeautifulSoup(html, "lxml")
        
        listing_id = self.extract_id_from_url(url, r'/(\d+)$')
        if not listing_id:
            return None
        
        # 嘗試從 JSON 提取所有數據
        json_data = self._extract_from_json(soup)
        
        # 基本信息 (優先 JSON)
        title = json_data.get('title') or self._extract_title(soup)
        listing_type = self._extract_listing_type(url)
        make = json_data.get('make') or None
        model = json_data.get('model') or None
        if not make or not model:
            make, model = self._extract_make_model(soup, title)
        year = json_data.get('year') or self._extract_year(soup, title)
        trim = json_data.get('trim')
        
        # 價格 (優先 JSON)
        price = json_data.get('price') or self._extract_price(soup)
        
        # 車輛規格 (優先 JSON)
        mileage = json_data.get('mileage') or self._extract_mileage(soup)
        body_type = json_data.get('body_type') or self._extract_body_type(soup)
        transmission = json_data.get('transmission') or self._extract_transmission(soup)
        fuel_type = json_data.get('fuel_type') or self._extract_fuel_type(soup)
        drivetrain = json_data.get('drivetrain') or self._extract_drivetrain(soup)
        color = json_data.get('color') or self._extract_color(soup)
        vin = self._extract_vin(soup)  # VIN 通常不在 JSON
        
        # 位置信息 (優先 JSON)
        location = json_data.get('location') or self._extract_location(soup)
        
        # 經銷商/賣家信息 (優先 JSON - 已在 _extract_seller 中實現)
        seller_type, seller_name, contact_phone = self._extract_seller(soup)
        
        # Promotions
        promotions = self._extract_promotions(soup)
        
        # 描述和特點 (優先 JSON)
        description = json_data.get('description') or self._extract_description(soup)
        features = json_data.get('features') or self._extract_features(soup)
        
        # 圖片 (優先 JSON)
        image_urls = json_data.get('image_urls') or self._extract_images(soup)
        
        # 發布日期
        post_date = self._extract_post_date(soup)
        
        return {
            'listing_id': listing_id,
            'url': url,
            'title': title,
            'listing_type': listing_type,
            'make': make,
            'model': model,
            'year': year,
            'trim': trim,
            'price': price,
            'mileage': mileage,
            'body_type': body_type,
            'transmission': transmission,
            'fuel_type': fuel_type,
            'drivetrain': drivetrain,
            'color': color,
            'vin': vin,
            'description': description,
            'features': self.to_json(features) if features else None,
            'seller_type': seller_type,
            'seller_name': seller_name,
            'contact_phone': contact_phone,
            'location': self.to_json(location) if isinstance(location, dict) else location,
            'promotions': self.to_json(promotions),
            'image_urls': self.to_json(image_urls),
            'post_date': post_date,
        }
    
    def _extract_from_json(self, soup: BeautifulSoup) -> Dict:
        """
        從 __NEXT_DATA__ JSON 提取所有可用數據
        
        JSON 結構 (基於 二手車項目頁頁schema.json):
        - makeName, modelName, year, trim
        - mileage, price
        - bodyTypeName, transmissionName, fuelTypeName, drivetrainName
        - color (id, name, hex)
        - description, imageHub.photos
        - contactInfo, user, dealer, salesperson
        """
        result = {}
        
        next_data = soup.find('script', id='__NEXT_DATA__')
        if not next_data or not next_data.string:
            return result
        
        try:
            data = json.loads(next_data.string)
            page_data = data.get('props', {}).get('pageProps', {}).get('data', {})
            
            if not page_data:
                return result
            
            # 基本信息
            result['title'] = page_data.get('title')
            result['make'] = page_data.get('makeName')
            result['model'] = page_data.get('modelName')
            result['year'] = page_data.get('year')
            result['trim'] = page_data.get('trim')
            result['price'] = page_data.get('price')
            result['mileage'] = page_data.get('mileage')
            
            # 車輛規格 - 從嵌套結構提取英文名
            result['body_type'] = page_data.get('bodyTypeName')
            
            transmission = page_data.get('transmissionName')
            if isinstance(transmission, dict):
                result['transmission'] = transmission.get('en')
            elif transmission:
                result['transmission'] = transmission
            
            fuel_type = page_data.get('fuelTypeName')
            if isinstance(fuel_type, dict):
                result['fuel_type'] = fuel_type.get('en')
            elif fuel_type:
                result['fuel_type'] = fuel_type
            
            drivetrain = page_data.get('drivetrainName')
            if isinstance(drivetrain, dict):
                result['drivetrain'] = drivetrain.get('en')
            elif drivetrain:
                result['drivetrain'] = drivetrain
            
            # 顏色
            color = page_data.get('color')
            if isinstance(color, dict):
                color_name = color.get('name', {})
                if isinstance(color_name, dict):
                    result['color'] = color_name.get('en')
                else:
                    result['color'] = color_name
            
            # 描述
            result['description'] = page_data.get('description')
            
            # 圖片
            image_hub = page_data.get('imageHub', {})
            if image_hub:
                result['image_urls'] = image_hub.get('photos', [])
            
            # 位置
            contact_info = page_data.get('contactInfo', {})
            if contact_info:
                result['location'] = {
                    'city': contact_info.get('cityName'),
                    'province': 'ON'
                }
            
            # 特點/配置
            other_specs = page_data.get('otherSpecifications', {})
            if other_specs:
                features = []
                for category in ['safeties', 'exteriors', 'interiors', 'multimedia']:
                    for item in other_specs.get(category, []):
                        if isinstance(item, dict):
                            en_name = item.get('en', '')
                            if en_name:
                                features.append(en_name)
                result['features'] = features
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            pass
        
        return result
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取標題"""
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            title = self.clean_text(self.extract_text(title_elem))
            # 清理網站後綴
            title = re.sub(r'\s*[-|_].*51.*$', '', title)
            title = re.sub(r'_车行直卖_?', '', title)
            title = re.sub(r'_私人转让_?', '', title)
            return title.strip()
        return ""
    
    def _extract_listing_type(self, url: str) -> str:
        """提取汽車類型"""
        if '/used-cars/' in url:
            return '二手'
        elif '/new-cars/' in url:
            return '新車'
        elif '/lease-cars/' in url:
            return '轉lease'
        return '二手'
    
    def _extract_make_model(self, soup: BeautifulSoup, title: str) -> tuple:
        """提取品牌和型號"""
        make = None
        model = None
        
        for brand in self.CAR_BRANDS:
            if brand.lower() in title.lower():
                make = brand
                # 提取型號
                pattern = rf'{brand}\s+(\w+)'
                model_match = re.search(pattern, title, re.I)
                if model_match:
                    model = model_match.group(1)
                break
        
        return make, model
    
    def _extract_year(self, soup: BeautifulSoup, title: str) -> Optional[int]:
        """提取年份"""
        year_match = re.search(r'(19\d{2}|20\d{2})', title)
        if year_match:
            return int(year_match.group(1))
        return None
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """提取價格"""
        # 查找價格元素
        price_elem = soup.find(class_=re.compile(r'price|cost'))
        if price_elem:
            text = price_elem.get_text()
            match = re.search(r'\$?([\d,]+)', text)
            if match:
                return float(match.group(1).replace(',', ''))
        
        # 從全文搜索
        text = soup.get_text()
        match = re.search(r'\$\s*([\d,]+)', text)
        if match:
            price = float(match.group(1).replace(',', ''))
            if 1000 <= price <= 500000:  # 合理價格範圍
                return price
        
        return None
    
    def _extract_mileage(self, soup: BeautifulSoup) -> Optional[int]:
        """提取里程（改進版 - 結合舊方法）"""
        text = soup.get_text()
        
        # 多種模式匹配
        patterns = [
            r'([\d,]+)\s*(?:km|公里|kilometres|KM)',
            r'里程[：:]\s*([\d,]+)',
            r'[Mm]ileage[：:\s]*([\d,]+)',
            r'Odometer[：:\s]*([\d,]+)',
            r'(\d{1,3}(?:,\d{3})*)\s*km',  # 格式如 150,000 km
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    mileage = int(match.group(1).replace(',', ''))
                    # 合理範圍檢查 (100 - 500000 km)
                    if 100 <= mileage <= 500000:
                        return mileage
                except:
                    pass
        
        # 舊方法備用：在表格或列表中查找
        for elem in soup.find_all(['td', 'dd', 'span', 'li']):
            text = elem.get_text()
            match = re.search(r'([\d,]+)\s*(?:km|公里)', text, re.I)
            if match:
                try:
                    mileage = int(match.group(1).replace(',', ''))
                    if 100 <= mileage <= 500000:
                        return mileage
                except:
                    pass
        
        return None
    
    def _extract_body_type(self, soup: BeautifulSoup) -> Optional[str]:
        """提取車身類型"""
        text = soup.get_text().lower()
        body_types = {
            'sedan': 'Sedan',
            'suv': 'SUV',
            'coupe': 'Coupe',
            'hatchback': 'Hatchback',
            'wagon': 'Wagon',
            'truck': 'Truck',
            'van': 'Van',
            'convertible': 'Convertible',
            '轎車': 'Sedan',
            '跑車': 'Coupe',
            '休旅車': 'SUV',
        }
        for key, value in body_types.items():
            if key in text:
                return value
        return None
    
    def _extract_transmission(self, soup: BeautifulSoup) -> Optional[str]:
        """提取變速箱"""
        text = soup.get_text().lower()
        if 'automatic' in text or '自動' in text or 'auto' in text:
            return 'Automatic'
        elif 'manual' in text or '手動' in text:
            return 'Manual'
        elif 'cvt' in text:
            return 'CVT'
        return None
    
    def _extract_fuel_type(self, soup: BeautifulSoup) -> Optional[str]:
        """提取燃料類型"""
        text = soup.get_text().lower()
        if 'electric' in text or '電動' in text or 'ev' in text:
            return 'Electric'
        elif 'hybrid' in text or '混合' in text:
            return 'Hybrid'
        elif 'diesel' in text or '柴油' in text:
            return 'Diesel'
        elif 'gas' in text or '汽油' in text:
            return 'Gasoline'
        return None
    
    def _extract_drivetrain(self, soup: BeautifulSoup) -> Optional[str]:
        """提取驅動方式"""
        text = soup.get_text().lower()
        if 'awd' in text or 'all wheel' in text or '全驅' in text:
            return 'AWD'
        elif '4wd' in text or '4x4' in text or '四驅' in text:
            return '4WD'
        elif 'fwd' in text or 'front wheel' in text or '前驅' in text:
            return 'FWD'
        elif 'rwd' in text or 'rear wheel' in text or '後驅' in text:
            return 'RWD'
        return None
    
    def _extract_color(self, soup: BeautifulSoup) -> Optional[str]:
        """提取顏色"""
        text = soup.get_text()
        match = re.search(r'(?:颜色|colour?|color)[：:\s]*(\S+)', text, re.I)
        if match:
            return match.group(1)
        return None
    
    def _extract_vin(self, soup: BeautifulSoup) -> Optional[str]:
        """提取VIN碼"""
        text = soup.get_text()
        # VIN 是17位字符
        match = re.search(r'VIN[：:\s]*([A-HJ-NPR-Z0-9]{17})', text, re.I)
        if match:
            return match.group(1)
        return None
    
    def _extract_location(self, soup: BeautifulSoup) -> Dict:
        """提取位置信息"""
        location = {'city': None, 'province': 'ON'}
        
        # 查找位置元素
        loc_elem = soup.find(class_=re.compile(r'location|address'))
        if loc_elem:
            text = loc_elem.get_text()
            # 常見城市
            cities = ['Toronto', 'Markham', 'Richmond Hill', 'Vaughan', 
                      'Mississauga', 'Scarborough', 'North York', 'Brampton',
                      'Kingston', 'Ottawa', 'Hamilton', 'London']
            for city in cities:
                if city.lower() in text.lower():
                    location['city'] = city
                    break
        
        return location
    
    def _extract_seller(self, soup: BeautifulSoup) -> tuple:
        """
        提取賣家信息（改進版 - 優先從 JSON 提取）
        
        JSON 結構:
        - user.mobile: 電話號碼 (明文)
        - user.name: 用戶名
        - contactInfo.contactName: 聯繫人名
        - dealer: 車行信息 (如有)
        - salesperson: 銷售人員 (如有)
        """
        seller_type = '私人'  # 默認私人
        seller_name = None
        contact_phone = None
        
        # 優先從 __NEXT_DATA__ JSON 提取
        next_data = soup.find('script', id='__NEXT_DATA__')
        if next_data and next_data.string:
            try:
                data = json.loads(next_data.string)
                page_data = data.get('props', {}).get('pageProps', {}).get('data', {})
                
                # 提取電話 - 優先順序: user.mobile > salesperson > dealer
                user = page_data.get('user', {})
                if user and user.get('mobile'):
                    phone = user.get('mobile', '')
                    if len(phone) == 10:
                        contact_phone = f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
                    else:
                        contact_phone = phone
                
                # 提取聯繫人名
                contact_info = page_data.get('contactInfo', {})
                if contact_info and contact_info.get('contactName'):
                    seller_name = contact_info.get('contactName')
                elif user and user.get('name'):
                    seller_name = user.get('name')
                
                # 判斷是否車行
                dealer = page_data.get('dealer')
                salesperson = page_data.get('salesperson')
                if dealer or salesperson:
                    seller_type = '車行'
                    if salesperson and salesperson.get('phone'):
                        phone = salesperson.get('phone', '')
                        if len(phone) == 10:
                            contact_phone = f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
                        else:
                            contact_phone = phone
                    if salesperson and salesperson.get('name'):
                        seller_name = salesperson.get('name')
                    elif dealer and dealer.get('name'):
                        seller_name = dealer.get('name')
                
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        
        # 後備方案：從 HTML 文本提取
        if not contact_phone:
            text = soup.get_text()
            
            # 方法1: 從 class 查找電話
            phone_elem = soup.find(class_=re.compile(r'phone|tel|contact'))
            if phone_elem:
                phone_text = phone_elem.get_text()
                match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', phone_text)
                if match:
                    contact_phone = match.group(1)
            
            # 方法2: 從全文用正則提取電話
            if not contact_phone:
                phone_patterns = [
                    r'(\d{3}[-.\s]\d{3}[-.\s]\d{4})',  # 416-555-1234
                    r'\((\d{3})\)\s*(\d{3})[-.\s](\d{4})',  # (416) 555-1234
                    r'(\d{10})',  # 4165551234
                ]
                for pattern in phone_patterns:
                    match = re.search(pattern, text)
                    if match:
                        if len(match.groups()) == 3:
                            contact_phone = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                        else:
                            phone = match.group(1).replace(' ', '').replace('.', '-')
                            if len(phone) == 10:
                                contact_phone = f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
                            else:
                                contact_phone = phone
                        break
            
            # 方法3: 查找 href="tel:" 連結
            if not contact_phone:
                tel_link = soup.find('a', href=re.compile(r'^tel:'))
                if tel_link:
                    phone = tel_link.get('href', '').replace('tel:', '').strip()
                    if phone:
                        contact_phone = phone
        
        return seller_type, seller_name, contact_phone
    
    def _extract_promotions(self, soup: BeautifulSoup) -> Dict:
        """
        提取 Promotions 標籤
        基於 二手車項目頁頁schema.json
        """
        promotions = {
            'same_day_approval': False,
            'no_credit_ok': False,
            'no_job_ok': False,
            'delivery_available': False,
            'warranty_available': False,
        }
        
        # 查找標籤元素
        text = soup.get_text().lower()
        
        for label, key in self.PROMOTION_LABELS.items():
            if label.lower() in text:
                promotions[key] = True
        
        # 額外檢查
        if '当天' in text and '批' in text:
            promotions['same_day_approval'] = True
        if '保修' in text or 'warranty' in text:
            promotions['warranty_available'] = True
        
        return promotions
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """提取描述"""
        desc_elem = soup.find(class_=re.compile(r'description|content|detail'))
        if desc_elem:
            for tag in desc_elem.find_all(['script', 'style']):
                tag.decompose()
            return self.clean_text(desc_elem.get_text())[:2000]
        return ""
    
    def _extract_features(self, soup: BeautifulSoup) -> List[str]:
        """提取特點/配置"""
        features = []
        feature_elem = soup.find(class_=re.compile(r'feature|option|equipment'))
        if feature_elem:
            for li in feature_elem.find_all('li'):
                features.append(self.clean_text(li.get_text()))
        return features[:30]
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """提取圖片"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('data-src') or img.get('src')
            if src and ('51img' in src or 'storage' in src):
                if 'logo' not in src and 'icon' not in src:
                    images.append(src)
        return list(set(images))[:20]
    
    def _extract_post_date(self, soup: BeautifulSoup) -> Optional[str]:
        """提取發布日期"""
        text = soup.get_text()
        
        # 相對時間
        match = re.search(r'(\d+)\s*天前', text)
        if match:
            days = int(match.group(1))
            return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        match = re.search(r'(\d+)\s*小時前', text)
        if match:
            hours = int(match.group(1))
            return (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d')
        
        # 絕對日期
        match = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', text)
        if match:
            return match.group(1).replace('/', '-')
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def save_item(self, data: Dict) -> bool:
        """保存汽車到資料庫（匹配 models.py 的 auto_listings 架構）"""
        try:
            # 繁體中文轉換
            title = self.to_traditional(data['title'])
            description = self.to_traditional(data['description'])
            features = self.to_traditional(data.get('features'))
            dealer_name = self.to_traditional(data.get('seller_name'))
            city = self.to_traditional(data.get('location'))
            color = self.to_traditional(data.get('color'))
            body_type = self.to_traditional(data.get('body_type'))
            
            # 處理 promotions
            promotions = data.get('promotions', {})
            if isinstance(promotions, str):
                import json
                try:
                    promotions = json.loads(promotions)
                except:
                    promotions = {}
            
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO auto_listings (
                    listing_id, url, title, listing_type, make, model, year,
                    body_type, color, transmission, drivetrain, fuel_type,
                    kilometers, price, city,
                    dealer_name, dealer_phone, vin,
                    features, description, images,
                    promo_same_day_approval, promo_no_credit_ok, promo_no_job_ok,
                    promo_delivery_available, promo_warranty_available,
                    post_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['listing_id'],
                data['url'],
                title,
                data.get('listing_type'),
                data.get('make'),
                data.get('model'),
                data.get('year'),
                body_type,
                color,
                data.get('transmission'),
                data.get('drivetrain'),
                data.get('fuel_type'),
                data.get('mileage'),  # mileage -> kilometers
                data.get('price'),
                city,
                dealer_name,
                data.get('contact_phone'),
                data.get('vin'),
                features,
                description,
                data.get('image_urls'),
                promotions.get('same_day_approval', 0),
                promotions.get('no_credit_ok', 0),
                promotions.get('no_job_ok', 0),
                promotions.get('delivery_available', 0),
                promotions.get('warranty_available', 0),
                data.get('post_date'),
            ))
            
            conn.commit()
            conn.close()
            self.logger.info(f"保存汽車: {title[:30]}...")
            return True
        except Exception as e:
            self.logger.error(f"保存汽車失敗: {e}")
            return False


if __name__ == "__main__":
    scraper = AutoScraper()
    scraper.run(max_pages=1000)  # 增加頁數以處理詳情頁
