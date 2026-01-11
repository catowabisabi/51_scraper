"""
51.ca 房屋爬蟲 (API 版)
使用 house.51.ca API 獲取 MLS 買賣 + 租房信息

API Endpoints:
- /api/v7/property?limit=20&page=1 - 房屋列表
- /api/v7/property/promoted/random?limit=6 - 推廣房屋
- transactionType: 1=買賣, 2=出租
"""

import re
import json
from typing import List, Dict, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper
from .models import get_connection


class HouseScraper(BaseScraper):
    """房屋爬蟲 - API 版"""
    
    SCRAPER_NAME = "house"
    BASE_URL = "https://house.51.ca"
    API_URL = "https://house.51.ca/api/v7"
    URL_TYPE = "house"
    
    # 房屋類型映射 (buildingType ID -> 名稱)
    BUILDING_TYPES = {
        1: '獨立屋',      # Detached
        2: '半獨立屋',    # Semi-Detached
        3: '鎮屋',        # Townhouse
        5: '聯排屋',      # Row/Townhouse
        6: '雙拼屋',      # Duplex
        7: '三拼屋',      # Triplex
        14: '平房',       # Bungalow
        17: '農場',       # Farm
        18: '公寓',       # Condo Apt
        19: '公寓鎮屋',   # Condo Townhouse
    }
    
    # 交易類型
    TRANSACTION_TYPES = {
        1: '買賣',
        2: '出租',
    }
    
    # 標籤映射
    TAGS = {
        1: '學區房',
        2: '華人超市',
        3: '公園',
        4: '近地鐵',
        5: '近商場',
    }
    
    # 面積映射 (approximateSf)
    SQFT_RANGES = {
        1: '0-499',
        2: '500-599',
        3: '600-699',
        4: '700-799',
        5: '800-899',
        6: '900-999',
        7: '1000-1099',
        8: '1100-1199',
        9: '1200-1399',
        10: '1400-1599',
        11: '1600-1799',
        12: '1800-1999',
        13: '2000-2249',
        14: '2250-2499',
        15: '2500-2999',
        16: '3000-3499',
        17: '3500-3999',
        18: '4000-4499',
        19: '4500-4999',
        20: '5000+',
    }
    
    def get_start_urls(self) -> List[str]:
        """獲取起始URL列表 - API 版本不需要"""
        return []
    
    def run(self, max_pages: int = 50, fetch_details: bool = False):
        """
        運行爬蟲 - API 版本
        直接從 API 獲取數據，不需要解析 HTML
        
        Args:
            max_pages: 最大頁數
            fetch_details: 是否獲取詳細資訊 (描述、經紀電話等)
        """
        self.logger.info("=" * 60)
        self.logger.info(f"開始運行 {self.SCRAPER_NAME} 爬蟲 (API 版)")
        self.logger.info(f"  - 獲取詳情: {'是' if fetch_details else '否'}")
        self.logger.info("=" * 60)
        
        # 初始化數據庫
        from .models import init_database
        init_database()
        
        start_time = datetime.now()
        total_saved = 0
        total_errors = 0
        
        # 獲取買賣房屋 (transactionType=1)
        self.logger.info("正在獲取買賣房屋...")
        saved, errors = self._fetch_properties(
            transaction_type=1, 
            max_pages=max_pages // 2,
            fetch_details=fetch_details
        )
        total_saved += saved
        total_errors += errors
        
        # 獲取出租房屋 (transactionType=2)
        self.logger.info("正在獲取出租房屋...")
        saved, errors = self._fetch_properties(
            transaction_type=2, 
            max_pages=max_pages // 2,
            fetch_details=fetch_details
        )
        total_saved += saved
        total_errors += errors
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        self.logger.info("=" * 60)
        self.logger.info("爬蟲運行統計:")
        self.logger.info(f"  - 項目保存: {total_saved}")
        self.logger.info(f"  - 錯誤數量: {total_errors}")
        self.logger.info(f"  - 運行時間: {elapsed:.2f} 秒")
        self.logger.info("=" * 60)
    
    def _fetch_properties(self, transaction_type: int = 1, max_pages: int = 25, fetch_details: bool = False) -> tuple:
        """
        從 API 獲取房屋列表
        
        Args:
            transaction_type: 1=買賣, 2=出租
            max_pages: 最大頁數
            fetch_details: 是否獲取詳細資訊
        
        Returns:
            (saved_count, error_count)
        """
        saved = 0
        errors = 0
        limit = 50  # 每頁數量
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{self.API_URL}/property"
                params = {
                    'limit': limit,
                    'page': page,
                    'transactionType': transaction_type,
                    'province': 'ontario',  # 只抓安省
                }
                
                response = requests.get(
                    url,
                    params=params,
                    headers={
                        'User-Agent': self.DEFAULT_HEADERS['User-Agent'],
                        'Accept': 'application/json',
                    },
                    timeout=30
                )
                
                if response.status_code != 200:
                    self.logger.error(f"API 錯誤: {response.status_code}")
                    errors += 1
                    continue
                
                data = response.json()
                
                if data.get('status') != 1:
                    self.logger.error(f"API 返回錯誤: {data.get('message')}")
                    errors += 1
                    continue
                
                properties = data.get('data', [])
                
                if not properties:
                    self.logger.info(f"頁面 {page} 沒有更多數據")
                    break
                
                for prop in properties:
                    try:
                        parsed = self._parse_api_property(prop, transaction_type)
                        if parsed:
                            # 如果需要詳情，獲取詳細資訊
                            if fetch_details:
                                detail = self._fetch_property_detail(parsed['listing_id'])
                                if detail:
                                    parsed.update(detail)
                            
                            if self.save_item(parsed):
                                saved += 1
                    except Exception as e:
                        self.logger.error(f"解析房屋失敗: {e}")
                        errors += 1
                
                self.logger.info(f"頁面 {page}: 獲取 {len(properties)} 個房屋")
                
                # 延遲避免請求過快
                import time
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"頁面 {page} 請求失敗: {e}")
                errors += 1
        
        return saved, errors
    
    def _fetch_property_detail(self, listing_id: str) -> Optional[Dict]:
        """
        從詳情 API 獲取房屋詳細資訊
        
        API: /api/v7/property/detail/{listingId}
        
        Returns:
            包含詳細資訊的字典，或 None
        """
        import time
        
        try:
            url = f"{self.API_URL}/property/detail/{listing_id}"
            
            response = requests.get(
                url,
                headers={
                    'User-Agent': self.DEFAULT_HEADERS['User-Agent'],
                    'Accept': 'application/json',
                },
                timeout=30
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if data.get('status') != 1:
                return None
            
            detail = data.get('data', {})
            
            # 解析詳情
            result = {}
            
            # 房源描述 (section6)
            description = detail.get('section6')
            if description:
                result['description'] = description.strip()
            
            # 完整圖片列表 (section1)
            section1 = detail.get('section1', {})
            photos = section1.get('photos', [])
            if photos:
                image_urls = [p.get('url') for p in photos if p.get('url')]
                result['image_urls'] = json.dumps(image_urls, ensure_ascii=False)
            
            # 經紀資訊 (listingAgents)
            listing_agents = detail.get('listingAgents')
            if listing_agents:
                if isinstance(listing_agents, list) and listing_agents:
                    agent = listing_agents[0]
                elif isinstance(listing_agents, dict):
                    agent = listing_agents
                else:
                    agent = None
                
                if agent:
                    result['agent_name'] = agent.get('name')
                    phones = agent.get('phone', [])
                    if phones:
                        result['agent_phone'] = phones[0] if isinstance(phones, list) else phones
            
            # 經紀公司 (listingBrokerage)
            brokerage = detail.get('listingBrokerage', {})
            if brokerage:
                result['agent_company'] = brokerage.get('name')
            
            # 座標 (section2)
            section2 = detail.get('section2', {})
            coordinate = section2.get('coordinate', {})
            if coordinate:
                result['lat'] = float(coordinate.get('lat', 0)) if coordinate.get('lat') else None
                result['lon'] = float(coordinate.get('lon', 0)) if coordinate.get('lon') else None
            
            # 房屋設施 (section5d1)
            section5d1 = detail.get('section5d1', {})
            features = []
            for group_key in ['g4', 'g6']:  # g4=設施, g6=建築設施
                group = section5d1.get(group_key, [])
                for item in group:
                    key = item.get('key')
                    value = item.get('value')
                    if key and value:
                        features.append(f"{key}: {value}")
            
            if features:
                result['features'] = json.dumps(features, ensure_ascii=False)
            
            # 延遲避免請求過快
            time.sleep(0.3)
            
            return result
            
        except Exception as e:
            self.logger.error(f"獲取詳情失敗 {listing_id}: {e}")
            return None

    def _parse_api_property(self, prop: Dict, transaction_type: int) -> Optional[Dict]:
        """
        解析 API 返回的房屋數據
        
        API 數據結構:
        - listingId: MLS 編號
        - transactionType: 1=買賣, 2=出租
        - propertyType: 房產類型 ID
        - buildingType: 建築類型 ID
        - listingPrice: 價格
        - bedrooms, dens, bathrooms: 房間數
        - location: {streetAddress, postalCode, community, city, province, unitNumber}
        - tags: 標籤 ID 列表
        - coverPage: 封面圖片 URL
        - approximateSf: 面積範圍 ID
        - totalParkingSpaces: 車位
        - relatedAgent: 相關經紀
        - listingBrokerage: 經紀公司
        """
        listing_id = prop.get('listingId')
        if not listing_id:
            return None
        
        location = prop.get('location', {})
        
        # 構建地址
        street_address = location.get('streetAddress', '')
        unit_number = location.get('unitNumber', '')
        if unit_number:
            full_address = f"{unit_number}-{street_address}"
        else:
            full_address = street_address
        
        # 構建 URL
        slug = prop.get('slug', '')
        if slug:
            detail_url = f"{self.BASE_URL}/{slug}"
        else:
            detail_url = f"{self.BASE_URL}/property/{listing_id}"
        
        # 解析房屋類型
        building_type_id = prop.get('buildingType')
        property_type = self.BUILDING_TYPES.get(building_type_id, '其他')
        
        # 解析交易類型
        listing_type = self.TRANSACTION_TYPES.get(transaction_type, '買賣')
        
        # 解析面積
        sqft_id = prop.get('approximateSf')
        sqft_range = self.SQFT_RANGES.get(sqft_id)
        sqft = None
        if sqft_range:
            # 取範圍的中間值
            if '+' in sqft_range:
                sqft = int(sqft_range.replace('+', ''))
            else:
                parts = sqft_range.split('-')
                if len(parts) == 2:
                    sqft = (int(parts[0]) + int(parts[1])) // 2
        
        # 解析標籤
        tag_ids = prop.get('tags', [])
        tags = []
        for tag_id in tag_ids:
            if isinstance(tag_id, int):
                tag_name = self.TAGS.get(tag_id)
                if tag_name:
                    tags.append(tag_name)
            elif isinstance(tag_id, dict):
                tag_name = tag_id.get('name')
                if tag_name:
                    tags.append(self.to_traditional(tag_name))
        
        # 經紀信息
        agent_name = None
        agent_company = None
        brokerage = prop.get('listingBrokerage', {})
        if brokerage:
            agent_company = brokerage.get('name')
        
        # 圖片
        cover_image = prop.get('coverPage')
        image_urls = [cover_image] if cover_image else []
        
        # 價格單位
        price = prop.get('listingPrice', 0)
        price_unit = '月' if transaction_type == 2 else '總價'
        
        # 標題
        city = location.get('city', '')
        bedrooms = prop.get('bedrooms', 0)
        title = f"{city} {property_type} {bedrooms}房"
        if unit_number:
            title = f"{city} {property_type} {bedrooms}房 #{unit_number}"
        
        return {
            'listing_id': listing_id,
            'url': detail_url,
            'title': title,
            'listing_type': listing_type,
            'property_type': property_type,
            'price': float(price) if price else None,
            'price_unit': price_unit,
            'address': full_address,
            'city': city,
            'province': location.get('province'),
            'community': location.get('community'),
            'postal_code': location.get('postalCode'),
            'bedrooms': prop.get('bedrooms'),
            'dens': prop.get('dens'),
            'bathrooms': prop.get('bathrooms'),
            'parking': prop.get('totalParkingSpaces'),
            'sqft': sqft,
            'description': None,  # API 列表不提供詳細描述
            'features': json.dumps(tags, ensure_ascii=False) if tags else None,
            'agent_name': agent_name,
            'agent_company': agent_company,
            'agent_phone': None,  # API 不直接提供
            'image_urls': json.dumps(image_urls, ensure_ascii=False) if image_urls else None,
            'listing_date': datetime.fromtimestamp(prop.get('listingAt', 0)).strftime('%Y-%m-%d') if prop.get('listingAt') else None,
            'lat': location.get('lat'),
            'lon': location.get('lon'),
        }
    
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面 - 保留備用"""
        return True
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """解析房屋列表頁面 - 不再使用，改用 API"""
        return []
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """解析房屋詳情頁面 - 保留備用"""
        return None
    
    def save_item(self, data: Dict) -> bool:
        """保存房屋到資料庫"""
        try:
            # 繁體中文轉換
            title = self.to_traditional(data.get('title'))
            address = self.to_traditional(data.get('address'))
            community = self.to_traditional(data.get('community'))
            description = self.to_traditional(data.get('description'))
            
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO house_listings (
                    listing_id, url, title, listing_type, property_type,
                    price, price_unit, address, city, province, community,
                    postal_code, bedrooms, dens, bathrooms, parking, sqft,
                    description, features,
                    agent_name, agent_phone, agent_company,
                    image_urls, listing_date, lat, lon
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('listing_id'),
                data.get('url'),
                title,
                data.get('listing_type'),
                data.get('property_type'),
                data.get('price'),
                data.get('price_unit'),
                address,
                data.get('city'),
                data.get('province'),
                community,
                data.get('postal_code'),
                data.get('bedrooms'),
                data.get('dens'),
                data.get('bathrooms'),
                data.get('parking'),
                data.get('sqft'),
                description,
                data.get('features'),
                data.get('agent_name'),
                data.get('agent_phone'),
                data.get('agent_company'),
                data.get('image_urls'),
                data.get('listing_date'),
                data.get('lat'),
                data.get('lon'),
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"保存房屋失敗: {e}")
            return False
    
    def update_missing_details(self, limit: int = 100):
        """
        更新現有記錄中缺少詳情的房屋
        
        Args:
            limit: 最多更新多少條
        """
        self.logger.info("=" * 60)
        self.logger.info(f"開始更新房屋詳情 (最多 {limit} 條)")
        self.logger.info("=" * 60)
        
        from .models import init_database
        init_database()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # 找出缺少描述的房屋
        cursor.execute("""
            SELECT listing_id FROM house_listings 
            WHERE description IS NULL OR description = ''
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            self.logger.info("沒有需要更新的房屋")
            return
        
        self.logger.info(f"找到 {len(rows)} 條需要更新的房屋")
        
        updated = 0
        errors = 0
        
        for (listing_id,) in rows:
            detail = self._fetch_property_detail(listing_id)
            if detail:
                # 更新資料庫
                conn = get_connection()
                cursor = conn.cursor()
                
                # 構建動態更新語句
                updates = []
                values = []
                for key, value in detail.items():
                    if value is not None:
                        updates.append(f"{key} = ?")
                        if key == 'description':
                            values.append(self.to_traditional(value))
                        else:
                            values.append(value)
                
                if updates:
                    values.append(listing_id)
                    sql = f"UPDATE house_listings SET {', '.join(updates)} WHERE listing_id = ?"
                    cursor.execute(sql, values)
                    conn.commit()
                    updated += 1
                
                conn.close()
            else:
                errors += 1
        
        self.logger.info("=" * 60)
        self.logger.info(f"更新完成: 成功 {updated}, 失敗 {errors}")
        self.logger.info("=" * 60)


if __name__ == "__main__":
    import sys
    
    scraper = HouseScraper()
    
    # 檢查命令行參數
    if len(sys.argv) > 1:
        if sys.argv[1] == '--details':
            # 獲取詳情模式
            scraper.run(max_pages=10, fetch_details=True)
        elif sys.argv[1] == '--update-details':
            # 更新現有記錄的詳情
            scraper.update_missing_details(limit=int(sys.argv[2]) if len(sys.argv) > 2 else 100)
        else:
            # 普通模式
            scraper.run(max_pages=int(sys.argv[1]))
    else:
        # 默認：快速獲取列表
        scraper.run(max_pages=10)
