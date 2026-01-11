"""
51.ca 集市爬蟲 (Playwright 無限滾動版)
使用 Playwright 模擬瀏覽器滾動，攔截網絡請求獲取更多數據

用法:
    python -m scrapers.market_scraper_playwright --category all --max-items 500
"""

import json
import time
import re
from typing import List, Dict, Optional
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Browser, Route

from .base import BaseScraper
from .models import get_connection


class MarketScraperPlaywright(BaseScraper):
    """集市爬蟲 - Playwright 無限滾動版本"""
    
    SCRAPER_NAME = "market_playwright"
    BASE_URL = "https://www.51.ca/market"
    
    # 集市分類
    CATEGORIES = [
        'all',
        'furniture', 'home-appliance', 'kitchen-supplies', 'mother-baby-products',
        'auto-parts', 'gardening', 'electronics', 'books', 'exerciser',
        'costume-matching', 'health', 'fruit-vegetable', 'musical-instruments',
        'bags-jewelry', 'pet-goods', 'others',
    ]
    
    def __init__(self):
        super().__init__()
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self._playwright = None
        self._collected_ids = set()
        self._all_items = []
        self._build_id = None
    
    # 實現抽象方法（Playwright 版不使用這些）
    def get_start_urls(self) -> List[str]:
        return [f"{self.BASE_URL}/all"]
    
    def is_list_page(self, url: str) -> bool:
        return True
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        return []
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        return None
    
    def _init_browser(self, headless: bool = True):
        """初始化瀏覽器"""
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=headless)
        self._page = self._browser.new_page()
        self._page.set_viewport_size({"width": 1280, "height": 800})
        
        # 設置請求攔截
        self._page.on("response", self._on_response)
    
    def _on_response(self, response):
        """攔截響應，捕獲 API 數據"""
        url = response.url
        
        # 捕獲 web/api/products POST 響應（無限滾動 API）
        if '/web/api/products' in url:
            try:
                if response.status == 200:
                    data = response.json()
                    items = data.get('data', [])
                    
                    if items:
                        new_count = 0
                        for item in items:
                            if item.get('source') == 'market':
                                item_id = item.get('id')
                                if item_id and item_id not in self._collected_ids:
                                    self._collected_ids.add(item_id)
                                    self._all_items.append(item)
                                    new_count += 1
                        
                        if new_count > 0:
                            self.logger.debug(f"攔截到 {new_count} 個新商品 (總計: {len(self._all_items)})")
            except Exception as e:
                self.logger.error(f"解析 API 響應失敗: {e}")
    
    def _close_browser(self):
        """關閉瀏覽器"""
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
    
    def _extract_items_from_page(self) -> List[Dict]:
        """從當前頁面提取 __NEXT_DATA__ 中的商品數據"""
        try:
            next_data = self._page.evaluate('''() => {
                const el = document.getElementById('__NEXT_DATA__');
                return el ? JSON.parse(el.textContent) : null;
            }''')
            
            if not next_data:
                return []
            
            # 保存 build ID
            self._build_id = next_data.get('buildId')
            
            init_data = next_data.get('props', {}).get('pageProps', {}).get('initData', {})
            items = init_data.get('data', [])
            
            # 過濾只要 market 來源
            return [item for item in items if item.get('source') == 'market']
        except Exception as e:
            self.logger.error(f"提取數據失敗: {e}")
            return []
    
    def _scroll_and_collect(self, max_items: int = 500, scroll_pause: float = 2.0) -> List[Dict]:
        """滾動頁面並收集數據"""
        # 先從初始頁面提取數據
        initial_items = self._extract_items_from_page()
        for item in initial_items:
            item_id = item.get('id')
            if item_id and item_id not in self._collected_ids:
                self._collected_ids.add(item_id)
                self._all_items.append(item)
        
        self.logger.info(f"初始頁面: {len(self._all_items)} 個商品")
        
        last_count = len(self._all_items)
        no_new_items_count = 0
        scroll_count = 0
        
        while len(self._all_items) < max_items:
            scroll_count += 1
            
            # 滾動到底部
            self._page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(scroll_pause)
            
            # 等待網絡請求完成
            try:
                self._page.wait_for_load_state('networkidle', timeout=5000)
            except:
                pass
            
            self.logger.info(f"滾動 #{scroll_count}: 已收集 {len(self._all_items)} 項")
            
            # 檢查是否有新數據
            if len(self._all_items) == last_count:
                no_new_items_count += 1
                if no_new_items_count >= 5:
                    self.logger.info("連續5次沒有新數據，停止滾動")
                    break
            else:
                no_new_items_count = 0
                last_count = len(self._all_items)
            
            # 額外安全檢查 - 最多滾動50次
            if scroll_count >= 50:
                self.logger.info("達到最大滾動次數")
                break
        
        return self._all_items
    
    def _fetch_detail(self, category_slug: str, item_id: int) -> Optional[Dict]:
        """獲取商品詳情"""
        try:
            build_id = self._build_id
            if not build_id:
                build_id = self._page.evaluate('''() => {
                    const el = document.getElementById('__NEXT_DATA__');
                    if (el) {
                        const data = JSON.parse(el.textContent);
                        return data.buildId;
                    }
                    return null;
                }''')
            
            if not build_id:
                return None
            
            url = f"{self.BASE_URL}/_next/data/{build_id}/{category_slug}/{item_id}.json"
            response = self._page.request.get(url)
            
            if response.status == 200:
                data = response.json()
                return data.get('pageProps', {}).get('data', {})
        except Exception as e:
            self.logger.error(f"獲取詳情失敗 {item_id}: {e}")
        return None
    
    def run(self, category: str = 'all', max_items: int = 500, 
            fetch_details: bool = False, headless: bool = True):
        """
        運行爬蟲
        
        Args:
            category: 分類 (all, furniture, etc.)
            max_items: 最大抓取數量
            fetch_details: 是否獲取詳情
            headless: 是否無頭模式
        """
        self.logger.info(f"開始爬取分類: {category}, 最大數量: {max_items}")
        
        try:
            self._init_browser(headless=headless)
            
            # 訪問列表頁
            url = f"{self.BASE_URL}/{category}"
            self.logger.info(f"訪問頁面: {url}")
            self._page.goto(url, wait_until='networkidle')
            
            # 等待頁面加載
            time.sleep(2)
            
            # 滾動並收集數據
            items = self._scroll_and_collect(max_items=max_items)
            
            self.logger.info(f"共收集 {len(items)} 個商品")
            
            # 保存數據
            saved = 0
            errors = 0
            
            for item in items:
                try:
                    # 如果需要詳情
                    if fetch_details:
                        cat_slug = item.get('categorySlug', category)
                        detail = self._fetch_detail(cat_slug, item['id'])
                        if detail:
                            item = detail
                        time.sleep(0.3)
                    
                    item_data = self._parse_product_json(item)
                    if item_data and self.save_item(item_data):
                        saved += 1
                    else:
                        errors += 1
                except Exception as e:
                    self.logger.error(f"處理商品失敗: {e}")
                    errors += 1
            
            self.logger.info(f"爬取完成: 保存 {saved}, 錯誤 {errors}")
            return saved, errors
            
        finally:
            self._close_browser()
    
    def _parse_product_json(self, product: Dict) -> Optional[Dict]:
        """從 JSON 解析商品"""
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
        
        # 位置
        location_info = product.get('locationInfo', {}) or {}
        location_id = location_info.get('id')
        location_zh = location_info.get('titleZh', '')
        location_en = location_info.get('titleEn', '') or product.get('locationTitleEn', '')
        
        # 分類
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
        
        return {
            'post_id': str(prod_id),
            'url': f"{self.BASE_URL}/{category_slug}/{prod_id}",
            'title': product.get('title', ''),
            'description': product.get('description', ''),
            'format_price': product.get('formatPrice', ''),
            'price': price,
            'original_price': original_price,
            'negotiable': product.get('negotiable', False),
            'condition': product.get('condition', 0),
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
            
            cursor.execute('''
                INSERT OR REPLACE INTO market_posts (
                    post_id, url, title, description, format_price, price, 
                    original_price, negotiable, condition, category_id, 
                    category_slug, category_name, location_id, location_zh, 
                    location_en, pickup_methods, contact_phone, email, 
                    wechat_no, wechat_qrcode, photos, user_uid, user_name, 
                    user_avatar, favorite_count, published_at, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('post_id'),
                data.get('url', ''),
                title,
                description,
                data.get('format_price', ''),
                data.get('price', 0),
                data.get('original_price'),
                data.get('negotiable', False),
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
            return True
        except Exception as e:
            self.logger.error(f"保存商品失敗: {e}")
            return False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='51.ca 集市爬蟲 (Playwright 無限滾動版)')
    parser.add_argument('--category', '-c', default='all', 
                        help='分類 (all, furniture, electronics, etc.)')
    parser.add_argument('--max-items', '-m', type=int, default=500, 
                        help='最大抓取數量')
    parser.add_argument('--details', '-d', action='store_true', 
                        help='獲取詳情頁（包含聯繫方式）')
    parser.add_argument('--show-browser', action='store_true',
                        help='顯示瀏覽器窗口（調試用）')
    args = parser.parse_args()
    
    scraper = MarketScraperPlaywright()
    scraper.run(
        category=args.category, 
        max_items=args.max_items, 
        fetch_details=args.details,
        headless=not args.show_browser
    )
