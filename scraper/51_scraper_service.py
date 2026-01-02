"""
51.ca 黃頁服務爬蟲
爬取 www.51.ca/service 的商家和服務信息
"""

import re
import json
from typing import List, Dict, Optional
from datetime import datetime

from bs4 import BeautifulSoup

from base_scraper import BaseScraper
from models import get_connection, add_url_to_queue


class ServiceScraper(BaseScraper):
    """黃頁服務爬蟲"""
    
    SCRAPER_NAME = "service_scraper"
    BASE_URL = "https://www.51.ca/service"
    URL_TYPE = "service"
    
    # 服務分類
    SERVICE_CATEGORIES = {
        'construction-renovation': '建筑装修',
        'garden-snow-removal-services': '园艺铲雪',
        'roofing': '专业屋顶',
        'doors-windows-inserts': '门窗玻璃',
        'mortgage': '贷款按揭',
        'heating-cooling-ventilating': '冷暖空调',
        'fence-deck': '围栏露台',
        'household-cleaning': '家居清洁',
        'electric-services': '电工电气',
        'pest-control': '捕兽杀虫',
        'cabinets-stone-materials': '枱柜石材',
        'glass-decoration-services': '玻璃装璜',
        'heat-preservation': '保温隔热',
        'garage-door-installation-maintenance-service': '车库门',
        'alarms-security-services': '防盗报警',
        'drain-plumbing': '通渠治漏',
        'interior-decoration': '室内设计',
        'paint-stucco': '油漆粉刷',
        'architectural-design': '建筑设计',
        'basement-construction-repair': '土库补漏',
        'floor-staircase': '地板楼梯',
        'household-appliances-repair': '家电维修',
        'pipe-services': '水管水喉',
        'demolish-rebuild-house-service': '拆房重建',
        'art-schools': '艺术教育',
        'after-school-tutorial': '课余补习',
        'continuing-education-training': '成人培训',
        'air-travel-ticket-agencies': '机票旅游',
        'funeral-services': '殡仪墓园',
        'moving-cartage': '搬运卸货',
        'transport-services': '接送服务',
        'driving-school': '考牌练车',
        'car-maintenance': '汽车维修',
        'car-insurance': '汽车保险',
        'notaries': '法律公证',
        'immigration-lawyers': '留学移民',
        'accounting-tax-consultants': '会计报税',
        'ei-applying': 'EI申请',
        'other-insurance': '各类保险',
        'chinese-medical-clinics': '中医诊所',
        'computer-services': '电脑服务',
        'internet-web-page-design': '网页设计',
        'freight-forwarding': '货运报关',
    }
    
    def get_start_urls(self) -> List[str]:
        """獲取起始URL列表"""
        urls = [f"{self.BASE_URL}/"]
        # 添加主要分類頁面
        for cat_key in list(self.SERVICE_CATEGORIES.keys())[:10]:
            urls.append(f"{self.BASE_URL}/categories/{cat_key}")
        return urls
    
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面"""
        # 詳情頁包含 /posts/ + 數字ID 或 /merchants/ + 數字ID
        if re.search(r'/posts/\d+', url) or re.search(r'/merchants/\d+', url):
            return False
        return True
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """解析服務列表頁面"""
        soup = BeautifulSoup(html, "lxml")
        items = []
        
        # 查找服務帖子連結
        # 帖子URL格式: https://www.51.ca/service/categories/xxx/posts/123456
        post_links = soup.find_all('a', href=re.compile(r'/service/categories/[^/]+/posts/\d+'))
        
        seen_urls = set()
        for link in post_links:
            href = link.get('href', '')
            if not href:
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
            
            items.append({'url': post_url, 'type': 'post'})
        
        # 查找商家連結
        merchant_links = soup.find_all('a', href=re.compile(r'/merchants/\d+'))
        for link in merchant_links:
            href = link.get('href', '')
            if not href:
                continue
            
            if href.startswith('/'):
                merchant_url = f"https://merchant.51.ca{href}"
            elif 'merchant.51.ca' in href:
                merchant_url = href
            else:
                continue
            
            merchant_url = merchant_url.split('?')[0]
            
            if merchant_url in seen_urls:
                continue
            seen_urls.add(merchant_url)
            
            items.append({'url': merchant_url, 'type': 'merchant'})
        
        self.logger.info(f"列表頁面發現 {len(items)} 個項目")
        return items
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """解析詳情頁面"""
        if '/merchants/' in url:
            return self._parse_merchant_page(html, url)
        else:
            return self._parse_post_page(html, url)
    
    def _parse_merchant_page(self, html: str, url: str) -> Optional[Dict]:
        """解析商家頁面"""
        soup = BeautifulSoup(html, "lxml")
        
        merchant_id = self.extract_id_from_url(url, r'/merchants/(\d+)')
        if not merchant_id:
            return None
        
        # 提取商家信息
        name = self._extract_merchant_name(soup)
        english_name = self._extract_english_name(soup)
        category, subcategory = self._extract_category(soup, url)
        description = self._extract_description(soup)
        services = self._extract_services(soup)
        address = self._extract_address(soup)
        phone = self._extract_phone(soup)
        website = self._extract_website(soup)
        logo_url = self._extract_logo(soup)
        image_urls = self._extract_images(soup)
        
        return {
            'merchant_id': merchant_id,
            'url': url,
            'name': name,
            'english_name': english_name,
            'category': category,
            'subcategory': subcategory,
            'description': description,
            'services': self.to_json(services),
            'address': address,
            'phone': phone,
            'website': website,
            'business_hours': None,
            'logo_url': logo_url,
            'image_urls': self.to_json(image_urls),
            'rating': None,
            'review_count': 0,
            'type': 'merchant'
        }
    
    def _parse_post_page(self, html: str, url: str) -> Optional[Dict]:
        """解析服務帖子頁面"""
        soup = BeautifulSoup(html, "lxml")
        
        post_id = self.extract_id_from_url(url, r'/posts/(\d+)')
        if not post_id:
            return None
        
        # 提取帖子信息
        title = self._extract_title(soup)
        category, subcategory = self._extract_category(soup, url)
        content = self._extract_content(soup)
        phone = self._extract_phone(soup)
        price = self._extract_price(soup)
        location = self._extract_location(soup)
        image_urls = self._extract_images(soup)
        
        # 嘗試提取關聯商家ID
        merchant_id = None
        merchant_link = soup.find('a', href=re.compile(r'/merchants/\d+'))
        if merchant_link:
            merchant_id = self.extract_id_from_url(merchant_link.get('href', ''), r'/merchants/(\d+)')
        
        return {
            'post_id': post_id,
            'url': url,
            'merchant_id': merchant_id,
            'title': title,
            'category': category,
            'subcategory': subcategory,
            'content': content,
            'contact_phone': phone,
            'price': price,
            'location': location,
            'image_urls': self.to_json(image_urls),
            'type': 'post'
        }
    
    def _extract_merchant_name(self, soup: BeautifulSoup) -> str:
        """提取商家名稱"""
        name_elem = soup.find('h1') or soup.find('title')
        if name_elem:
            name = self.clean_text(self.extract_text(name_elem))
            name = re.sub(r'\s*[-|].*$', '', name)
            return name
        return ""
    
    def _extract_english_name(self, soup: BeautifulSoup) -> str:
        """提取英文名稱"""
        text = soup.get_text()
        # 通常英文名在中文名後面
        match = re.search(r'[\u4e00-\u9fff]+\s+([A-Za-z][A-Za-z\s&]+(?:Inc|Ltd|Corp)?\.?)', text)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取標題"""
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            return self.clean_text(self.extract_text(title_elem))
        return ""
    
    def _extract_category(self, soup: BeautifulSoup, url: str) -> tuple:
        """提取分類"""
        category = None
        subcategory = None
        
        # 從URL提取
        for cat_key, cat_name in self.SERVICE_CATEGORIES.items():
            if cat_key in url:
                category = cat_name
                break
        
        return category, subcategory
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """提取描述"""
        desc_elem = soup.find(class_=re.compile(r'description|content|detail|intro'))
        if desc_elem:
            return self.clean_text(self.extract_text(desc_elem))[:2000]
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取內容"""
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        
        content_elem = soup.find('article') or soup.find('main') or soup.find(class_='content')
        if content_elem:
            return self.clean_text(content_elem.get_text(separator='\n', strip=True))[:3000]
        return ""
    
    def _extract_services(self, soup: BeautifulSoup) -> List[str]:
        """提取服務項目"""
        services = []
        
        # 查找主營業務
        text = soup.get_text()
        if '主营业务' in text or '主營業務' in text:
            # 嘗試提取列表項
            service_items = soup.find_all(['li', 'span'], string=re.compile(r'^[\u4e00-\u9fff]{2,10}$'))
            for item in service_items[:20]:
                service = self.extract_text(item)
                if service and len(service) <= 15:
                    services.append(service)
        
        return services
    
    def _extract_address(self, soup: BeautifulSoup) -> str:
        """提取地址"""
        addr_elem = soup.find(class_=re.compile(r'address|location'))
        if addr_elem:
            return self.clean_text(self.extract_text(addr_elem))
        return None
    
    def _extract_phone(self, soup: BeautifulSoup) -> str:
        """提取電話"""
        text = soup.get_text()
        phone_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', text)
        if phone_match:
            return phone_match.group(1)
        return None
    
    def _extract_website(self, soup: BeautifulSoup) -> str:
        """提取網站"""
        website_link = soup.find('a', href=re.compile(r'^https?://(?!.*51\.ca)'))
        if website_link:
            return website_link.get('href')
        return None
    
    def _extract_logo(self, soup: BeautifulSoup) -> str:
        """提取Logo"""
        logo_img = soup.find('img', class_=re.compile(r'logo'))
        if logo_img:
            src = logo_img.get('src') or logo_img.get('data-src')
            if src:
                if src.startswith('//'):
                    return 'https:' + src
                return src
        return None
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """提取圖片"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and not any(x in src.lower() for x in ['logo', 'icon', 'avatar', 'button']):
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://www.51.ca' + src
                if src.startswith('http'):
                    images.append(src)
        return images[:10]
    
    def _extract_price(self, soup: BeautifulSoup) -> str:
        """提取價格"""
        text = soup.get_text()
        price_match = re.search(r'\$[\d,.]+', text)
        if price_match:
            return price_match.group(0)
        return None
    
    def _extract_location(self, soup: BeautifulSoup) -> str:
        """提取位置"""
        text = soup.get_text()
        locations = ['士嘉堡', '北约克', '万锦', '列治文山', '密西沙加', 
                     '多伦多', '大多地区', 'Scarborough', 'North York', 
                     'Markham', 'Richmond Hill', 'Mississauga', 'Toronto']
        for loc in locations:
            if loc in text:
                return loc
        return None
    
    def save_item(self, data: Dict) -> bool:
        """保存項目"""
        if data.get('type') == 'merchant':
            return self._save_merchant(data)
        else:
            return self._save_post(data)
    
    def _save_merchant(self, data: Dict) -> bool:
        """保存商家"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO service_merchants 
                (merchant_id, url, name, english_name, category, subcategory,
                 description, services, address, phone, website, business_hours,
                 logo_url, image_urls, rating, review_count, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('merchant_id'),
                data.get('url'),
                data.get('name'),
                data.get('english_name'),
                data.get('category'),
                data.get('subcategory'),
                data.get('description'),
                data.get('services'),
                data.get('address'),
                data.get('phone'),
                data.get('website'),
                data.get('business_hours'),
                data.get('logo_url'),
                data.get('image_urls'),
                data.get('rating'),
                data.get('review_count', 0),
                datetime.now()
            ))
            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"保存商家失敗: {e}")
            return False
        finally:
            conn.close()
    
    def _save_post(self, data: Dict) -> bool:
        """保存服務帖子"""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO service_posts 
                (post_id, url, merchant_id, title, category, subcategory,
                 content, contact_phone, price, location, image_urls, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('post_id'),
                data.get('url'),
                data.get('merchant_id'),
                data.get('title'),
                data.get('category'),
                data.get('subcategory'),
                data.get('content'),
                data.get('contact_phone'),
                data.get('price'),
                data.get('location'),
                data.get('image_urls'),
                datetime.now()
            ))
            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"保存帖子失敗: {e}")
            return False
        finally:
            conn.close()
    
    def run_service_scraper(self, max_pages: int = 50):
        """運行服務爬蟲"""
        start_urls = self.get_start_urls()
        self.run(start_urls=start_urls, max_pages=max_pages)


def main():
    """主函數"""
    scraper = ServiceScraper(headless=True)
    scraper.run_service_scraper(max_pages=30)


if __name__ == "__main__":
    main()
