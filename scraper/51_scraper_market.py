"""
51.ca 集市爬蟲 (Next.js 版本)
爬取 www.51.ca/market 的二手交易信息
直接從 __NEXT_DATA__ JSON 提取數據
"""

import re
import json
from typing import List, Dict, Optional
from datetime import datetime

from bs4 import BeautifulSoup

from base_scraper import BaseScraper
from models import get_connection, add_url_to_queue


class MarketScraper(BaseScraper):
    """集市爬蟲 - 針對 Next.js 網站結構，從 __NEXT_DATA__ 提取數據"""
    
    SCRAPER_NAME = "market_scraper"
    BASE_URL = "https://www.51.ca/market"
    URL_TYPE = "market"
    
    # 集市分類
    MARKET_CATEGORIES = [
        '',  # 首頁
        'furniture', 
        'home-appliance',
        'kitchen-supplies',
        'mother-baby-products',
        'auto-parts',
        'gardening',
        'electronics',
        'books',
        'exerciser',
        'costume-matching',
        'health',
        'fruit-vegetable',
        'musical-instruments',
        'bags-jewelry',
        'pet-goods',
        'others',
    ]
    
    def get_start_urls(self) -> List[str]:
        """獲取起始URL列表 - 只需要列表頁，因為列表頁包含完整數據"""
        urls = []
        for cat in self.MARKET_CATEGORIES:
            if cat:
                urls.append(f"{self.BASE_URL}/{cat}")
            else:
                urls.append(f"{self.BASE_URL}/")
        return urls
    
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面"""
        # 詳情頁格式: /market/category/數字ID
        if re.search(r'/market/[^/]+/\d+$', url):
            return False
        return True
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """解析集市列表頁面 - 直接從 __NEXT_DATA__ 提取所有商品資訊並保存"""
        soup = BeautifulSoup(html, "lxml")
        items = []
        saved_count = 0
        
        # 從 __NEXT_DATA__ 提取資料
        next_data = soup.find('script', id='__NEXT_DATA__')
        if not next_data:
            self.logger.warning(f"找不到 __NEXT_DATA__: {url}")
            return items
        
        try:
            data = json.loads(next_data.string)
            props = data.get('props', {}).get('pageProps', {})
            
            # 商品列表在 initData.data 中
            init_data = props.get('initData', {})
            products = init_data.get('data', [])
            
            # 過濾只要 market 來源的商品 (排除 auto, discount 等)
            market_products = [p for p in products if p.get('source') == 'market']
            
            self.logger.info(f"從 __NEXT_DATA__ 提取到 {len(market_products)} 個集市商品")
            
            # 直接保存每個商品
            for product in market_products:
                try:
                    item_data = self._parse_product_from_json(product)
                    if item_data and self.save_item(item_data):
                        saved_count += 1
                except Exception as e:
                    self.logger.error(f"解析商品失敗: {e}")
            
            self.logger.info(f"成功保存 {saved_count} 個商品")
            
            # 查找分頁連結 (如果需要爬取更多頁面)
            pagination = init_data.get('pagination', {})
            current_page = pagination.get('page', 1)
            last_page = pagination.get('lastPage', 1)
            
            if current_page < last_page and current_page < 5:  # 限制最多5頁
                next_page_url = f"{url}?page={current_page + 1}"
                items.append({'url': next_page_url})
                self.logger.info(f"添加下一頁: {next_page_url}")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"解析 JSON 失敗: {e}")
        except Exception as e:
            self.logger.error(f"解析列表頁失敗: {e}")
        
        return items
    
    def _parse_product_from_json(self, product: Dict) -> Optional[Dict]:
        """從 JSON 物件解析商品資料"""
        if not product or not isinstance(product, dict):
            return None
        
        prod_id = product.get('id')
        if not prod_id:
            return None
        
        # 價格
        price_str = product.get('formatPrice', '0')
        try:
            price = float(price_str.replace(',', ''))
        except ValueError:
            price = 0
        
        # 圖片 - 過濾只要商品圖片
        photos = product.get('photos', [])
        image_urls = [p for p in photos if p and ('storage.51yun.ca' in p or 'p0.51img.ca' in p)]
        
        # 位置
        location = product.get('locationTitleEn', '')
        
        # 分類
        category = product.get('categorySlug', '')
        
        # 商家資訊
        merchant = product.get('merchant')
        seller_info = ''
        if merchant:
            seller_info = f"商家: {merchant.get('title', '')}"
        
        # 狀態 (從描述推斷)
        description = product.get('description', '')
        condition = self._infer_condition(description)
        
        return {
            'post_id': str(prod_id),
            'url': f"{self.BASE_URL}/{category}/{prod_id}",
            'title': product.get('title', ''),
            'category': category,
            'price': price,
            'original_price': None,
            'condition': condition,
            'description': description,
            'location': location,
            'contact_info': seller_info,
            'image_urls': self.to_json(image_urls),
            'post_date': product.get('publishedAt', ''),
            'view_count': 0,
        }
    
    def _infer_condition(self, text: str) -> str:
        """從描述推斷物品狀態"""
        text_lower = text.lower()
        if '全新' in text or 'new' in text_lower or '未拆' in text:
            return '全新'
        elif '九成新' in text or '9成新' in text or '95%新' in text or '9.5成新' in text:
            return '九成新'
        elif '八成新' in text or '8成新' in text:
            return '八成新'
        elif '二手' in text or 'used' in text_lower:
            return '二手'
        return ''
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """解析集市詳情頁面 - 從 __NEXT_DATA__ 提取"""
        soup = BeautifulSoup(html, "lxml")
        
        next_data = soup.find('script', id='__NEXT_DATA__')
        if not next_data:
            self.logger.warning(f"找不到 __NEXT_DATA__: {url}")
            return None
        
        try:
            data = json.loads(next_data.string)
            props = data.get('props', {}).get('pageProps', {})
            product = props.get('data', {})
            
            if not product:
                self.logger.warning(f"找不到商品資料: {url}")
                return None
            
            return self._parse_detail_product(product, url)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"解析 JSON 失敗: {e}")
            return None
        except Exception as e:
            self.logger.error(f"解析詳情頁失敗: {e}")
            return None
    
    def _parse_detail_product(self, product: Dict, url: str) -> Dict:
        """解析詳情頁的商品資料"""
        # 從 URL 提取 ID
        match = re.search(r'/(\d+)$', url)
        post_id = match.group(1) if match else str(product.get('id', ''))
        
        # 分類
        category_info = product.get('categoryInfo', {})
        category = category_info.get('titleCn') or category_info.get('slug', '')
        
        # 位置
        location_info = product.get('locationInfo', {})
        location = location_info.get('titleZh') or location_info.get('titleEn', '')
        
        # 賣家
        user_info = product.get('user', {})
        seller_name = user_info.get('name', '')
        
        # 圖片
        photos = product.get('photos', [])
        image_urls = [p for p in photos if p and 'storage.51yun.ca' in p]
        
        # 狀態
        condition_map = {1: '全新', 2: '二手', 3: '九成新'}
        condition = condition_map.get(product.get('condition'), '')
        
        # 取貨方式
        pickup_map = {1: '自提', 2: '可郵寄', 3: '自提或郵寄'}
        pickup_methods = product.get('pickupMethods', [])
        pickup_str = ', '.join([pickup_map.get(m, '') for m in pickup_methods if m in pickup_map])
        
        # 價格
        price_str = product.get('formatPrice', '0')
        try:
            price = float(price_str.replace(',', ''))
        except ValueError:
            price = 0
        
        contact_info = f"賣家: {seller_name}"
        if pickup_str:
            contact_info += f"; {pickup_str}"
        
        return {
            'post_id': post_id,
            'url': url,
            'title': product.get('title', ''),
            'category': category,
            'price': price,
            'original_price': None,
            'condition': condition,
            'description': product.get('description', ''),
            'location': location,
            'contact_info': contact_info.strip('; '),
            'image_urls': self.to_json(image_urls),
            'post_date': product.get('publishedAt', ''),
            'view_count': product.get('favoriteCount', 0),
        }
    
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
            self.logger.info(f"保存集市帖子: {data.get('title', 'N/A')[:30]}")
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
