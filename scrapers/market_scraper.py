"""
51.ca 集市爬蟲 (整合版)
爬取 www.51.ca/market 的二手物品交易信息
使用 Next.js __NEXT_DATA__ JSON 提取數據

Schema 來源: data_structures_人類defined/二手物件買賣.json
數據結構: props.pageProps.data 包含完整商品信息
"""

import re
import json
from typing import List, Dict, Optional
from datetime import datetime

from bs4 import BeautifulSoup

from .base import BaseScraper
from .models import get_connection


class MarketScraper(BaseScraper):
    """集市爬蟲 - Next.js 網站結構"""
    
    SCRAPER_NAME = "market"
    BASE_URL = "https://www.51.ca/market"
    URL_TYPE = "market"
    
    # 集市分類
    CATEGORIES = [
        '',              # 首頁
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
    
    def get_start_urls(self) -> List[str]:
        """獲取起始URL列表"""
        urls = []
        for cat in self.CATEGORIES:
            if cat:
                urls.append(f"{self.BASE_URL}/{cat}")
            else:
                urls.append(f"{self.BASE_URL}/")
        return urls
    
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面"""
        # 詳情頁: /market/category/數字ID
        if re.search(r'/market/[^/]+/\d+$', url):
            return False
        return True
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """
        解析集市列表頁面
        直接從 __NEXT_DATA__ 提取所有商品並保存
        """
        soup = BeautifulSoup(html, "lxml")
        items = []
        saved_count = 0
        
        # 從 __NEXT_DATA__ 提取
        next_data = soup.find('script', id='__NEXT_DATA__')
        if not next_data:
            self.logger.warning(f"找不到 __NEXT_DATA__: {url}")
            return items
        
        try:
            data = json.loads(next_data.string)
            props = data.get('props', {}).get('pageProps', {})
            
            # 商品列表在 initData.data
            init_data = props.get('initData', {})
            products = init_data.get('data', [])
            
            # 過濾只要 market 來源
            market_products = [p for p in products if p.get('source') == 'market']
            
            self.logger.info(f"從 __NEXT_DATA__ 提取到 {len(market_products)} 個商品")
            
            # 直接保存每個商品
            for product in market_products:
                try:
                    item_data = self._parse_product_json(product)
                    if item_data and self.save_item(item_data):
                        saved_count += 1
                except Exception as e:
                    self.logger.error(f"解析商品失敗: {e}")
            
            self.logger.info(f"成功保存 {saved_count} 個商品")
            
            # 分頁處理
            pagination = init_data.get('pagination', {})
            current_page = pagination.get('page', 1)
            last_page = pagination.get('lastPage', 1)
            
            if current_page < last_page and current_page < 5:
                next_page_url = f"{url.split('?')[0]}?page={current_page + 1}"
                items.append({'url': next_page_url})
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失敗: {e}")
        
        return items
    
    def _parse_product_json(self, product: Dict) -> Optional[Dict]:
        """
        從 JSON 解析商品
        基於 二手物件買賣.json schema
        """
        if not product:
            return None
        
        prod_id = product.get('id')
        if not prod_id:
            return None
        
        # 價格
        price_str = product.get('formatPrice', '0')
        try:
            price = float(price_str.replace(',', '').replace('$', ''))
        except ValueError:
            price = 0
        
        # 原價/折扣價
        original_price = None
        discount_str = product.get('discountPrice', '')
        if discount_str:
            try:
                original_price = float(discount_str.replace(',', '').replace('$', ''))
            except ValueError:
                pass
        
        # 圖片
        photos = product.get('photos', [])
        image_urls = [p for p in photos if p and 
                      ('storage.51yun.ca' in p or 'p0.51img.ca' in p)]
        
        # 位置 (locationInfo)
        location_info = product.get('locationInfo', {})
        location = location_info.get('titleEn', '') or location_info.get('titleZh', '')
        if not location:
            location = product.get('locationTitleEn', '')
        
        # 分類 (categoryInfo)
        category_info = product.get('categoryInfo', {})
        category = category_info.get('slug', '') or product.get('categorySlug', '')
        category_name = category_info.get('titleCn', '')
        
        # 用戶信息
        user_info = product.get('user', {})
        seller_name = user_info.get('name', '')
        seller_id = user_info.get('uid', '')
        
        # 商家信息
        merchant = product.get('merchant')
        if merchant:
            seller_name = f"商家: {merchant.get('title', '')}"
        
        # 聯絡方式
        contact_info = {
            'phone': product.get('encryptPhone', ''),
            'email': product.get('email', ''),
            'wechat': product.get('wechatNo', ''),
        }
        
        # 狀態
        condition = self._parse_condition(product.get('condition', 0))
        
        # 描述
        description = product.get('description', '')
        
        # 是否可議價
        negotiable = product.get('negotiable', False)
        
        return {
            'post_id': str(prod_id),
            'url': f"{self.BASE_URL}/{category}/{prod_id}",
            'title': product.get('title', ''),
            'category': category,
            'category_name': category_name,
            'price': price,
            'original_price': original_price,
            'negotiable': negotiable,
            'condition': condition,
            'description': description,
            'location': location,
            'seller_name': seller_name,
            'seller_id': str(seller_id) if seller_id else None,
            'contact_info': self.to_json(contact_info),
            'image_urls': self.to_json(image_urls),
            'post_date': product.get('publishedAt', ''),
            'view_count': 0,
            'favorite_count': product.get('favoriteCount', 0),
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
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """
        解析詳情頁面
        從 __NEXT_DATA__ props.pageProps.data 提取
        """
        soup = BeautifulSoup(html, "lxml")
        
        next_data = soup.find('script', id='__NEXT_DATA__')
        if not next_data:
            return None
        
        try:
            data = json.loads(next_data.string)
            props = data.get('props', {}).get('pageProps', {})
            product = props.get('data', {})
            
            if not product:
                return None
            
            return self._parse_product_json(product)
            
        except Exception as e:
            self.logger.error(f"解析詳情頁失敗: {e}")
            return None
    
    def save_item(self, data: Dict) -> bool:
        """保存商品到資料庫"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # 轉換為繁體中文
            title = self.to_traditional(data.get('title', ''))
            description = self.to_traditional(data.get('description', ''))
            condition = self.to_traditional(data.get('condition', ''))
            category_name = self.to_traditional(data.get('category_name', ''))
            
            cursor.execute("""
                INSERT OR REPLACE INTO market_posts (
                    post_id, url, title, description, format_price, price,
                    original_price, negotiable, condition, category_slug, category_name,
                    location_en, contact_phone, email, wechat_no, photos,
                    user_uid, user_name, favorite_count, published_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['post_id'],
                data['url'],
                title,
                description,
                str(data.get('price', 0)),
                data.get('price', 0),
                data.get('original_price'),
                1 if data.get('negotiable') else 0,
                condition,
                data.get('category'),
                category_name,
                data.get('location'),
                data.get('contact_info', {}).get('phone') if isinstance(data.get('contact_info'), dict) else None,
                data.get('contact_info', {}).get('email') if isinstance(data.get('contact_info'), dict) else None,
                data.get('contact_info', {}).get('wechat') if isinstance(data.get('contact_info'), dict) else None,
                data['image_urls'],
                data.get('seller_id'),
                self.to_traditional(data.get('seller_name', '')),
                data.get('favorite_count', 0),
                data.get('post_date'),
            ))
            
            conn.commit()
            conn.close()
            self.logger.debug(f"保存商品: {title[:30]}...")
            return True
        except Exception as e:
            self.logger.error(f"保存商品失敗: {e}")
            return False


if __name__ == "__main__":
    scraper = MarketScraper()
    scraper.run(max_pages=30)
