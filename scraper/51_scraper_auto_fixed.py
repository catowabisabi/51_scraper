"""
51.ca 汽車爬蟲 - 修正版本
爬取 auto.51.ca 的汽車交易信息
"""

import re
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from base_scraper import BaseScraper
from models import get_connection, add_url_to_queue


class AutoScraper(BaseScraper):
    """汽車爬蟲"""
    
    SCRAPER_NAME = "auto_scraper"
    BASE_URL = "https://www.51.ca/autos"
    URL_TYPE = "auto"
    
    # 汽車品牌
    CAR_BRANDS = [
        'Toyota', 'Honda', 'Nissan', 'Mazda', 'BMW', 'Mercedes', 'Audi',
        'Lexus', 'Acura', 'Infiniti', 'Ford', 'Chevrolet', 'Hyundai',
        'Kia', 'Volkswagen', 'Subaru', 'Tesla', 'Porsche', 'Jeep'
    ]
    
    def get_start_urls(self) -> List[str]:
        """獲取起始URL列表"""
        return [
            f"{self.BASE_URL}/",
            f"{self.BASE_URL}/used-cars",
            f"{self.BASE_URL}/new-cars",
            f"{self.BASE_URL}/lease-cars",
        ]
    
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面"""
        # 詳情頁格式: /autos/used-cars/數字ID 或 /autos/new-cars/數字ID
        if re.search(r'/autos/(used-cars|new-cars|lease-cars)/\d+$', url):
            return False
        return True
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """解析汽車列表頁面"""
        soup = BeautifulSoup(html, "lxml")
        items = []
        
        # 查找汽車連結 - 格式: /autos/used-cars/數字ID
        car_links = soup.find_all('a', href=re.compile(r'/autos/(used-cars|new-cars|lease-cars)/\d+'))
        
        seen_urls = set()
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
        
        self.logger.info(f"列表頁面發現 {len(items)} 個汽車")
        return items
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """解析汽車詳情頁面"""
        soup = BeautifulSoup(html, "lxml")
        
        listing_id = self.extract_id_from_url(url, r'/(\d+)$')
        if not listing_id:
            return None
        
        # 提取汽車信息
        title = self._extract_title(soup)
        listing_type = self._extract_listing_type(url, soup)
        make, model = self._extract_make_model(soup, title)
        year = self._extract_year(soup, title)
        price = self._extract_price(soup)
        mileage = self._extract_mileage(soup)
        body_type = self._extract_body_type(soup)
        transmission = self._extract_transmission(soup)
        fuel_type = self._extract_fuel_type(soup)
        color = self._extract_color(soup)
        vin = self._extract_vin(soup)
        description = self._extract_description(soup)
        features = self._extract_features(soup)
        seller_type = self._extract_seller_type(soup)
        seller_name = self._extract_seller_name(soup)
        contact_phone = self._extract_phone(soup)
        location = self._extract_location(soup)
        post_date = self._extract_post_date(soup)
        image_urls = self._extract_images(soup)
        
        return {
            'listing_id': listing_id,
            'url': url,
            'title': title,
            'listing_type': listing_type,
            'make': make,
            'model': model,
            'year': year,
            'price': price,
            'mileage': mileage,
            'body_type': body_type,
            'transmission': transmission,
            'fuel_type': fuel_type,
            'color': color,
            'vin': vin,
            'description': description,
            'features': self.to_json(features),
            'seller_type': seller_type,
            'seller_name': seller_name,
            'contact_phone': contact_phone,
            'location': location,
            'post_date': post_date,
            'image_urls': self.to_json(image_urls),
        }

    def _extract_listing_type(self, url: str, soup: BeautifulSoup) -> str:
        """提取汽車類型"""
        # 從URL路徑判斷
        if '/used-cars/' in url:
            return '二手'
        elif '/new-cars/' in url:
            return '新車'  
        elif '/lease-cars/' in url:
            return '轉lease'
        elif '/market/auto-parts/' in url:
            return '汽車配件'
            
        # 從頁面內容判斷
        text = soup.get_text().lower()
        if '二手车' in text or '二手車' in text or 'used car' in text:
            return '二手'
        elif '新车' in text or '新車' in text or 'new car' in text:
            return '新車'
        elif 'lease' in text:
            return '轉lease'
        elif '配件' in text or 'parts' in text:
            return '汽車配件'
            
        return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取標題"""
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            title = self.clean_text(self.extract_text(title_elem))
            # 移除網站名稱
            title = re.sub(r'\s*[-|_].*51.*$', '', title)
            # 移除重複的 "_年份_品牌_型號_車行直賣_" 格式
            title = re.sub(r'_\d{4}_[A-Za-z]+_[A-Za-z0-9]+_车行直卖_?', '', title)
            title = re.sub(r'_车行直卖_?', '', title)
            title = re.sub(r'_私人转让_?', '', title)
            return title.strip()
        return ""
    
    def _extract_make_model(self, soup: BeautifulSoup, title: str) -> tuple:
        """提取品牌和型號"""
        make = None
        model = None
        
        # 清理標題中的重複部分
        clean_title = re.sub(r'_\d{4}_[A-Za-z]+_[A-Za-z0-9]+_车行直卖_?', '', title)
        clean_title = re.sub(r'_车行直卖_?', '', clean_title)
        
        # 從標題中提取品牌
        for brand in self.CAR_BRANDS:
            if brand.lower() in clean_title.lower():
                make = brand
                # 提取型號 (品牌後面的單詞)
                pattern = rf'{brand}\s+(\w+)'
                model_match = re.search(pattern, clean_title, re.I)
                if model_match:
                    model = model_match.group(1)
                break
        
        # 從頁面中查找
        if not make:
            make_elem = soup.find(class_=re.compile(r'make|brand'))
            if make_elem:
                make = self.clean_text(self.extract_text(make_elem))
        
        return make, model
    
    def _extract_year(self, soup: BeautifulSoup, title: str) -> int:
        """提取年份"""
        # 從標題中提取
        year_match = re.search(r'(19\d{2}|20\d{2})', title)
        if year_match:
            return int(year_match.group(1))
        
        # 從頁面中查找
        text = soup.get_text()
        year_match = re.search(r'[年Year][\s:]*(\d{4})', text, re.I)
        if year_match:
            return int(year_match.group(1))
        
        return None

    def _extract_price(self, soup: BeautifulSoup) -> float:
        """提取價格"""
        text = soup.get_text()
        
        # 匹配各種價格格式
        patterns = [
            r'\$\s*([\d,]+(?:\.\d{2})?)',  # $24,888
            r'价格[：:\s]*\$?([\d,]+)',     # 價格：$24,888
            r'售价[：:\s]*\$?([\d,]+)',     # 售价：24888
            r'Price[：:\s]*\$?([\d,]+)',    # Price: $24,888
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    price_str = match.group(1).replace(',', '')
                    return float(price_str)
                except ValueError:
                    continue
        
        return None
    
    def _extract_mileage(self, soup: BeautifulSoup) -> int:
        """提取里程"""
        text = soup.get_text()
        # 匹配各種里程格式
        patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*(?:km|公里)',
            r'里程[：:]\s*(\d{1,3}(?:,\d{3})*)',
            r'mileage[：:]\s*(\d{1,3}(?:,\d{3})*)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    return int(match.group(1).replace(',', ''))
                except ValueError:
                    pass
        return None
    
    def _extract_body_type(self, soup: BeautifulSoup) -> str:
        """提取車身類型"""
        body_types = {
            'SUV': ['SUV', 'suv'],
            '轿车': ['Sedan', 'sedan', '轿车'],
            '跑车': ['Coupe', 'coupe', '跑车', 'sports'],
            '皮卡': ['Pickup', 'pickup', 'Truck', 'truck', '皮卡'],
            'MPV': ['Van', 'van', 'MPV', 'minivan', '商务车'],
            '掀背': ['Hatchback', 'hatchback', '两厢'],
            '敞篷': ['Convertible', 'convertible', '敞篷'],
        }
        
        text = soup.get_text().lower()
        for body_type, keywords in body_types.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return body_type
        return None
    
    def _extract_transmission(self, soup: BeautifulSoup) -> str:
        """提取變速箱類型"""
        text = soup.get_text().lower()
        if 'automatic' in text or '自动' in text or '自動' in text:
            return '自动'
        elif 'manual' in text or '手动' in text or '手動' in text:
            return '手动'
        elif 'cvt' in text:
            return 'CVT'
        return None
    
    def _extract_fuel_type(self, soup: BeautifulSoup) -> str:
        """提取燃料類型"""
        text = soup.get_text().lower()
        if 'electric' in text or '电动' in text or '純電' in text:
            return '纯电动'
        elif 'hybrid' in text or '混合' in text or '混动' in text:
            return '混合动力'
        elif 'diesel' in text or '柴油' in text:
            return '柴油'
        elif 'gas' in text or '汽油' in text:
            return '汽油'
        return None
    
    def _extract_color(self, soup: BeautifulSoup) -> str:
        """提取顏色"""
        colors = {
            '白': ['white', '白'],
            '黑': ['black', '黑'],
            '银': ['silver', '银', '銀'],
            '灰': ['grey', 'gray', '灰'],
            '红': ['red', '红', '紅'],
            '蓝': ['blue', '蓝', '藍'],
            '绿': ['green', '绿', '綠'],
            '金': ['gold', '金'],
            '棕': ['brown', '棕'],
        }
        
        text = soup.get_text().lower()
        for color_name, keywords in colors.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return color_name
        return None

    def _extract_vin(self, soup: BeautifulSoup) -> str:
        """提取VIN碼"""
        text = soup.get_text()
        
        # VIN碼格式：17位字母數字組合（排除I、O、Q）
        vin_patterns = [
            r'VIN[：:\s]*([A-HJ-NPR-Z0-9]{17})',
            r'车架号[：:\s]*([A-HJ-NPR-Z0-9]{17})',
            r'Vehicle Identification Number[：:\s]*([A-HJ-NPR-Z0-9]{17})',
            r'([A-HJ-NPR-Z0-9]{17})'  # 直接匹配17位VIN格式
        ]
        
        for pattern in vin_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                potential_vin = match.group(1)
                # 驗證VIN格式
                if len(potential_vin) == 17 and not re.search(r'[IOQ]', potential_vin, re.I):
                    return potential_vin
                    
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """提取描述"""
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        
        desc_elem = soup.find(class_=re.compile(r'description|content|detail'))
        if desc_elem:
            return self.clean_text(desc_elem.get_text(separator='\n', strip=True))[:2000]
        return ""
    
    def _extract_features(self, soup: BeautifulSoup) -> List[str]:
        """提取配置特點"""
        features = []
        
        feature_keywords = [
            '天窗', 'sunroof', '真皮', 'leather', '导航', 'navigation',
            '倒车影像', 'backup camera', '蓝牙', 'bluetooth', '加热座椅',
            'heated seats', '全景天窗', 'panoramic', 'AWD', '四驱',
            'CarPlay', 'Android Auto', '自动泊车', 'parking assist'
        ]
        
        text = soup.get_text().lower()
        for feature in feature_keywords:
            if feature.lower() in text:
                features.append(feature)
        
        return features
    
    def _extract_seller_type(self, soup: BeautifulSoup) -> str:
        """提取賣家類型"""
        text = soup.get_text().lower()
        if 'dealer' in text or '车行' in text or '車行' in text:
            return '车行'
        elif 'private' in text or '私人' in text or '个人' in text:
            return '私人'
        return None

    def _extract_seller_name(self, soup: BeautifulSoup) -> str:
        """提取賣家名稱"""
        # 從車行信息中提取
        text = soup.get_text()
        
        # 查找車行名稱
        dealer_names = [
            '11 Motors', 'Weilai Automotive', 'YST Auto Sales', 'KS Auto',
            'Toronto Auto', 'Richmond Auto', 'Elite Motors', 'Prime Auto'
        ]
        
        for name in dealer_names:
            if name.lower() in text.lower():
                return name
        
        # 從頁面結構中提取
        seller_elem = soup.find(class_=re.compile(r'dealer|seller|merchant|business'))
        if seller_elem:
            seller_text = self.clean_text(self.extract_text(seller_elem))
            if seller_text and len(seller_text) < 50:
                return seller_text[:100]
                
        return None
    
    def _extract_phone(self, soup: BeautifulSoup) -> str:
        """提取電話"""
        text = soup.get_text()
        phone_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', text)
        if phone_match:
            return phone_match.group(1)
        return None

    def _extract_location(self, soup: BeautifulSoup) -> str:
        """提取位置"""
        text = soup.get_text()
        
        # 匹配常見的加拿大城市
        canadian_cities = [
            'Toronto', 'Mississauga', 'Brampton', 'Hamilton', 'London', 'Markham',
            'Vaughan', 'Kitchener', 'Windsor', 'Richmond Hill', 'Oakville', 
            'Burlington', 'Barrie', 'Oshawa', 'Cambridge', 'Kingston', 'Whitby',
            'Guelph', 'Ajax', 'Thunder Bay', 'Chatham', 'Waterloo', 'Brantford',
            'Pickering', 'Sarnia', 'Sault Ste. Marie', 'North York', 'Scarborough',
            'Etobicoke', 'York', 'East York', 'Newmarket', 'Aurora', 'Milton',
            'Georgetown', 'Bradford', 'Innisfil', 'King', 'Whitchurch-Stouffville',
            'Richmond Hill', 'Thornhill', 'Unionville', 'Woodbridge'
        ]
        
        for city in canadian_cities:
            if city.lower() in text.lower():
                return city
                
        # 查找位置相關的元素
        loc_elem = soup.find(class_=re.compile(r'location|address|area|city'))
        if loc_elem:
            location_text = self.clean_text(self.extract_text(loc_elem))
            if location_text and len(location_text) < 50:
                return location_text
                
        return None

    def _extract_post_date(self, soup: BeautifulSoup) -> str:
        """提取發布時間"""
        text = soup.get_text()
        
        # 匹配各種時間格式
        time_patterns = [
            r'(\d+)\s*小时前',           # X小时前  
            r'(\d+)\s*hours?\s*ago',    # X hours ago
            r'(\d+)\s*天前',            # X天前
            r'(\d+)\s*days?\s*ago',     # X days ago
            r'(\d+)\s*分钟前',          # X分钟前
            r'(\d+)\s*minutes?\s*ago',  # X minutes ago
            r'昨天',                    # 昨天
            r'yesterday',               # yesterday
            r'今天',                    # 今天
            r'today'                    # today
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                if '小时前' in match.group(0) or 'hours ago' in match.group(0):
                    hours = int(match.group(1)) if match.group(1) else 0
                    post_time = datetime.now() - timedelta(hours=hours)
                    return post_time.strftime('%Y-%m-%d %H:%M:%S')
                elif '天前' in match.group(0) or 'days ago' in match.group(0):
                    days = int(match.group(1)) if match.group(1) else 0
                    post_time = datetime.now() - timedelta(days=days)
                    return post_time.strftime('%Y-%m-%d %H:%M:%S')
                elif '分钟前' in match.group(0) or 'minutes ago' in match.group(0):
                    minutes = int(match.group(1)) if match.group(1) else 0
                    post_time = datetime.now() - timedelta(minutes=minutes)
                    return post_time.strftime('%Y-%m-%d %H:%M:%S')
                elif '昨天' in match.group(0) or 'yesterday' in match.group(0):
                    post_time = datetime.now() - timedelta(days=1)
                    return post_time.strftime('%Y-%m-%d %H:%M:%S')
                elif '今天' in match.group(0) or 'today' in match.group(0):
                    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
        return None
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """提取汽車圖片 - 從 JavaScript、背景圖片和 img 標籤提取"""
        images = []
        seen = set()
        
        # 排除的路徑關鍵字 (UI元素、圖標等)
        exclude_keywords = [
            'logo', 'icon', 'avatar', 'button', 'ad', 'static-maps', 
            'placeholder', 'loading', 'assets/images', 'common/', 
            'detail/', 'radio_', 'checkbox', 'carfax', 'bell.png',
            'test-driv', 'empty', 'search', 'svg', 'default',
            'dealer-logo', 'salesperson'
        ]
        
        # 1. 從 JavaScript 提取 (最完整的來源)
        for script in soup.find_all('script'):
            text = script.string or ''
            if 'auto-car-photos' in text:
                # 提取所有 auto-car-photos URL
                urls = re.findall(r'https?://storage\.51yun\.ca/auto-car-photos/[^"\']+\.(?:jpg|jpeg|png|webp)', text, re.I)
                for url in urls:
                    if url not in seen:
                        images.append(url)
                        seen.add(url)
        
        # 2. 從 CSS background-image 提取 (備用)
        if not images:
            bg_pattern = re.compile(r'url\(["\']?(https?://[^"\'()]+)["\']?\)')
            for elem in soup.find_all(style=True):
                style = elem.get('style', '')
                for match in bg_pattern.finditer(style):
                    url = match.group(1)
                    if url in seen:
                        continue
                    if any(x in url.lower() for x in exclude_keywords):
                        continue
                    if 'storage.51yun.ca' in url and 'auto-car-photos' in url:
                        images.append(url)
                        seen.add(url)
        
        # 3. 從 img 標籤提取 (備用)
        if not images:
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if not src or src in seen:
                    continue
                
                if any(x in src.lower() for x in exclude_keywords):
                    continue
                
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    continue
                
                if not src.startswith('http'):
                    continue
                
                if 'storage.51yun.ca' in src and 'auto-car-photos' in src:
                    images.append(src)
                    seen.add(src)
        
        return images[:20]
    
    def save_item(self, data: Dict) -> bool:
        """保存汽車信息"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO auto_listings 
                (listing_id, url, title, listing_type, make, model, year, price, mileage,
                 body_type, transmission, fuel_type, color, vin, description,
                 features, seller_type, seller_name, contact_phone, location,
                 image_urls, post_date, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('listing_id'),
                data.get('url'),
                data.get('title'),
                data.get('listing_type'),
                data.get('make'),
                data.get('model'),
                data.get('year'),
                data.get('price'),
                data.get('mileage'),
                data.get('body_type'),
                data.get('transmission'),
                data.get('fuel_type'),
                data.get('color'),
                data.get('vin'),
                data.get('description'),
                data.get('features'),
                data.get('seller_type'),
                data.get('seller_name'),
                data.get('contact_phone'),
                data.get('location'),
                data.get('image_urls'),
                data.get('post_date'),
                datetime.now()
            ))
            conn.commit()
            self.logger.info(f"保存汽車: {data.get('title', 'N/A')}")
            return True
        except Exception as e:
            self.logger.error(f"保存汽車失敗: {e}")
            return False
        finally:
            conn.close()
    
    def run_auto_scraper(self, max_pages: int = 50):
        """運行汽車爬蟲"""
        start_urls = self.get_start_urls()
        self.run(start_urls=start_urls, max_pages=max_pages)


def main():
    """主函數"""
    scraper = AutoScraper(headless=True)
    scraper.run_auto_scraper(max_pages=30)


if __name__ == "__main__":
    main()