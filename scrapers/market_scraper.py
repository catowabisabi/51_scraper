"""
51.ca 集市爬蟲 (API版)
爬取 www.51.ca/market 的二手物品交易信息
使用 Next.js /_next/data API 提取數據

API格式:
- 列表: https://www.51.ca/market/_next/data/{buildId}/all.json?page=N
- 分類: https://www.51.ca/market/_next/data/{buildId}/{category}.json?page=N
- 詳情: https://www.51.ca/market/_next/data/{buildId}/{category}/{id}.json
"""

import re
import json
import time
from typing import List, Dict, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper
from .models import get_connection


class MarketScraper(BaseScraper):
    """集市爬蟲 - Next.js API 版本"""
    
    SCRAPER_NAME = "market"
    BASE_URL = "https://www.51.ca/market"
    URL_TYPE = "market"
    
    # 集市分類
    CATEGORIES = [
        'all',           # 全部
        'furniture',     # 家具
        'home-appliance', # 家電
        'kitchen-supplies', # 廚具
        'mother-baby-products', # 母嬰
        'auto-parts',    # 汽車配件
        'gardening',     # 園藝
        'electronics',   # 電子產品
        'books',         # 書籍
        'exerciser',     # 運動器材
        'costume-matching', # 服飾配件
        'health',        # 保健
        'fruit-vegetable', # 蔬果
        'musical-instruments', # 樂器
        'bags-jewelry',  # 包袋首飾
        'pet-goods',     # 寵物用品
        'others',        # 其他
    ]
    
    def __init__(self):
        super().__init__()
        self._build_id = None
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html',
        })
    
    def _get_build_id(self) -> Optional[str]:
        """獲取 Next.js buildId"""
        if self._build_id:
            return self._build_id
        
        try:
            r = self._session.get(f"{self.BASE_URL}/", timeout=15)
            soup = BeautifulSoup(r.text, 'lxml')
            next_data = soup.find('script', id='__NEXT_DATA__')
            if next_data:
                data = json.loads(next_data.string)
                self._build_id = data.get('buildId', '')
                self.logger.info(f"獲取 buildId: {self._build_id}")
                return self._build_id
        except Exception as e:
            self.logger.error(f"獲取 buildId 失敗: {e}")
        return None
    
    def _fetch_page_html(self, url: str) -> Optional[Dict]:
        """通過 HTML 頁面獲取數據（用於分頁）"""
        try:
            r = self._session.get(url, timeout=15)
            if r.status_code != 200:
                return None
            
            soup = BeautifulSoup(r.text, 'lxml')
            next_data = soup.find('script', id='__NEXT_DATA__')
            if next_data:
                data = json.loads(next_data.string)
                return data.get('props', {}).get('pageProps', {})
        except Exception as e:
            self.logger.error(f"獲取頁面失敗: {url} - {e}")
        return None
    
    def _fetch_detail_api(self, category: str, item_id: int) -> Optional[Dict]:
        """通過 API 獲取商品詳情"""
        build_id = self._get_build_id()
        if not build_id:
            return None
        
        url = f"{self.BASE_URL}/_next/data/{build_id}/{category}/{item_id}.json"
        try:
            r = self._session.get(url, timeout=10)
            if r.status_code == 200 and 'json' in r.headers.get('Content-Type', ''):
                data = r.json()
                return data.get('pageProps', {}).get('data', {})
        except Exception as e:
            self.logger.error(f"獲取詳情失敗: {item_id} - {e}")
        return None

    
    def run(self, categories: List[str] = None, max_pages: int = 5, fetch_details: bool = False):
        """
        運行爬蟲
        
        Args:
            categories: 要爬取的分類列表，None 則爬取全部
            max_pages: 每個分類最大頁數
            fetch_details: 是否獲取詳情頁（包含聯繫方式）
        """
        categories = categories or ['all']  # 默認只爬 all
        total_saved = 0
        total_errors = 0
        
        for category in categories:
            self.logger.info(f"開始爬取分類: {category}")
            
            for page in range(1, max_pages + 1):
                if category == 'all':
                    url = f"{self.BASE_URL}/all?page={page}"
                else:
                    url = f"{self.BASE_URL}/{category}?page={page}"
                
                self.logger.info(f"爬取頁面: {url}")
                
                page_data = self._fetch_page_html(url)
                if not page_data:
                    self.logger.warning(f"無法獲取頁面數據: {url}")
                    break
                
                init_data = page_data.get('initData', {})
                products = init_data.get('data', [])
                pagination = init_data.get('pagination', {})
                
                # 過濾只要 market 來源（排除 auto 等）
                market_products = [p for p in products if p.get('source') == 'market']
                
                self.logger.info(f"頁 {page}: 找到 {len(market_products)} 個集市商品")
                
                if not market_products:
                    break
                
                for product in market_products:
                    try:
                        # 如果需要詳情，獲取完整信息
                        if fetch_details:
                            cat_slug = product.get('categorySlug', category)
                            detail = self._fetch_detail_api(cat_slug, product['id'])
                            if detail:
                                product = detail
                            time.sleep(0.3)  # 避免請求過快
                        
                        item_data = self._parse_product_json(product)
                        if item_data and self.save_item(item_data):
                            total_saved += 1
                        else:
                            total_errors += 1
                    except Exception as e:
                        self.logger.error(f"處理商品失敗: {e}")
                        total_errors += 1
                
                # 檢查是否還有更多頁面
                current_page = pagination.get('page', page)
                last_page = pagination.get('lastPage', 1)
                
                if current_page >= last_page:
                    self.logger.info(f"已到達最後一頁: {current_page}/{last_page}")
                    break
                
                time.sleep(0.5)  # 頁面間延遲
        
        self.logger.info(f"爬取完成: 保存 {total_saved}, 錯誤 {total_errors}")
        return total_saved, total_errors
    
    def get_start_urls(self) -> List[str]:
        """獲取起始URL列表（兼容舊接口）"""
        return [f"{self.BASE_URL}/all"]
    
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面"""
        if re.search(r'/market/[^/]+/\d+$', url):
            return False
        return True
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """兼容舊接口"""
        return []
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """兼容舊接口 - 解析詳情頁"""
        soup = BeautifulSoup(html, "lxml")
        next_data = soup.find('script', id='__NEXT_DATA__')
        if not next_data:
            return None
        try:
            data = json.loads(next_data.string)
            product = data.get('props', {}).get('pageProps', {}).get('data', {})
            if product:
                return self._parse_product_json(product)
        except Exception as e:
            self.logger.error(f"解析詳情頁失敗: {e}")
        return None
    
    def _parse_product_json(self, product: Dict) -> Optional[Dict]:
        """
        從 JSON 解析商品
        """
        if not product:
            return None
        
        prod_id = product.get('id')
        if not prod_id:
            return None
        
        # 價格
        price_str = product.get('formatPrice', '0')
        try:
            price = float(str(price_str).replace(',', '').replace('$', ''))
        except ValueError:
            price = 0
        
        # 原價/折扣價
        original_price = None
        discount_str = product.get('discountPrice', '')
        if discount_str:
            try:
                original_price = float(str(discount_str).replace(',', '').replace('$', ''))
            except ValueError:
                pass
        
        # 圖片
        photos = product.get('photos', [])
        image_urls = [p for p in photos if p and 
                      ('storage.51yun.ca' in p or 'p0.51img.ca' in p)]
        
        # 位置 (locationInfo 可能在詳情頁中)
        location_info = product.get('locationInfo', {}) or {}
        location_id = location_info.get('id')
        location_zh = location_info.get('titleZh', '')
        location_en = location_info.get('titleEn', '') or product.get('locationTitleEn', '')
        
        # 分類 (categoryInfo 可能在詳情頁中)
        category_info = product.get('categoryInfo', {}) or {}
        category_id = category_info.get('id')
        category_slug = category_info.get('slug', '') or product.get('categorySlug', '')
        category_name = category_info.get('titleCn', '')
        
        # 用戶信息
        user_info = product.get('user', {}) or {}
        user_uid = user_info.get('uid')
        user_name = user_info.get('name', '')
        user_avatar = user_info.get('avatar', '')
        
        # 商家信息
        merchant = product.get('merchant')
        if merchant:
            user_name = f"商家: {merchant.get('title', '')}"
        
        # 取貨方式
        pickup_methods = product.get('pickupMethods', [])
        
        # 狀態碼
        condition_code = product.get('condition', 0)
        
        return {
            'post_id': str(prod_id),
            'url': f"{self.BASE_URL}/{category_slug}/{prod_id}",
            'title': product.get('title', ''),
            'description': product.get('description', ''),
            'format_price': product.get('formatPrice', ''),
            'price': price,
            'original_price': original_price,
            'negotiable': product.get('negotiable', False),
            'condition': condition_code,
            'category_id': category_id,
            'category_slug': category_slug,
            'category_name': category_name,
            'location_id': location_id,
            'location_zh': location_zh,
            'location_en': location_en,
            'pickup_methods': json.dumps(pickup_methods) if pickup_methods else None,
            'contact_phone': product.get('encryptPhone', ''),
            'email': product.get('email', ''),
            'wechat_no': product.get('wechatNo', ''),
            'wechat_qrcode': product.get('wechatQrcode', ''),
            'photos': json.dumps(image_urls) if image_urls else None,
            'user_uid': user_uid,
            'user_name': user_name,
            'user_avatar': user_avatar,
            'favorite_count': product.get('favoriteCount', 0),
            'published_at': product.get('publishedAt', ''),
            'source': product.get('source', 'market'),
        }
    
    def _parse_condition(self, condition: int) -> str:
        """解析物品狀態碼"""
        conditions = {
            0: '',
            1: '全新',
            2: '九成新',
            3: '八成新',
            4: '二手',
            5: '較舊',
        }
        return conditions.get(condition, '')
    
    def save_item(self, data: Dict) -> bool:
        """保存商品到資料庫"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # 轉換為繁體中文
            title = self.to_traditional(data.get('title', ''))
            description = self.to_traditional(data.get('description', ''))
            category_name = self.to_traditional(data.get('category_name', ''))
            user_name = self.to_traditional(data.get('user_name', ''))
            location_zh = self.to_traditional(data.get('location_zh', ''))
            
            cursor.execute("""
                INSERT OR REPLACE INTO market_posts (
                    post_id, url, title, description, format_price, price,
                    original_price, negotiable, condition, category_id, category_slug, category_name,
                    location_id, location_zh, location_en, pickup_methods,
                    contact_phone, email, wechat_no, wechat_qrcode, photos,
                    user_uid, user_name, user_avatar, favorite_count, published_at, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['post_id'],
                data['url'],
                title,
                description,
                data.get('format_price', ''),
                data.get('price', 0),
                data.get('original_price'),
                1 if data.get('negotiable') else 0,
                data.get('condition', 0),
                data.get('category_id'),
                data.get('category_slug', ''),
                category_name,
                data.get('location_id'),
                location_zh,
                data.get('location_en', ''),
                data.get('pickup_methods'),
                data.get('contact_phone', ''),
                data.get('email', ''),
                data.get('wechat_no', ''),
                data.get('wechat_qrcode', ''),
                data.get('photos'),
                data.get('user_uid'),
                user_name,
                data.get('user_avatar', ''),
                data.get('favorite_count', 0),
                data.get('published_at', ''),
                data.get('source', 'market'),
            ))
            
            conn.commit()
            conn.close()
            self.logger.debug(f"保存商品: {title[:30]}...")
            return True
        except Exception as e:
            self.logger.error(f"保存商品失敗: {e}")
            return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='51.ca 集市爬蟲')
    parser.add_argument('--category', '-c', default=None, 
                        help='分類 (all, furniture, electronics, etc.) 不指定則爬取全部分類')
    parser.add_argument('--pages', '-p', type=int, default=1, 
                        help='每個分類最大頁數 (注意: 目前分頁API不工作，只能獲取第1頁)')
    parser.add_argument('--details', '-d', action='store_true', 
                        help='獲取詳情頁（包含聯繫方式）')
    parser.add_argument('--all-categories', '-a', action='store_true',
                        help='爬取所有分類（而非只爬 all）')
    args = parser.parse_args()
    
    scraper = MarketScraper()
    
    if args.all_categories:
        # 爬取所有分類（除了 'all'，因為 'all' 包含的和其他分類重複）
        categories = [c for c in MarketScraper.CATEGORIES if c != 'all']
    elif args.category:
        categories = [args.category]
    else:
        categories = ['all']
    
    scraper.run(categories=categories, max_pages=args.pages, fetch_details=args.details)
