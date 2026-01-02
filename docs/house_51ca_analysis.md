# house.51.ca 房屋詳情頁面結構分析

## 1. 有效的房源頁面 URL

### MLS 房源（二手房/出租）
- **格式**: `https://house.51.ca/rental/ontario/{city}/{area}/{id}`
- **範例**: `https://house.51.ca/rental/ontario/toronto/north-york/604800`
- **MLS# 範例**: C12654644

### 租房列表
- **格式**: `https://house.51.ca/rental/ontario/{city}/{area}/{id}`
- **範例**: `https://house.51.ca/rental/ontario/toronto/scarborough/604816`

### 新房樓花
- **格式**: `https://house.51.ca/newhome/{city}/{area}/{project-name}`
- **範例**: `https://house.51.ca/newhome/toronto/toronto-downtown/the-millwood-toronto-on`

---

## 2. HTML 結構與 CSS 選擇器

### MLS 詳情頁面（如 rental/ontario/... 頁面）

#### 標題/地址
```html
<h3>1112 - 5858 YONGE Street</h3>
<!-- 或在詳情區塊中 -->
<div class="property-title">公寓 Toronto, Ontario M2M 3T3</div>
```
- **CSS 選擇器**: `h3` 或 `.property-title`

#### 價格
```html
<span>$ 2,650出租</span>
<!-- 或 -->
<span>$680 /月</span>
```
- **CSS 選擇器**: 搜索包含 `$` 符號的文本

#### 臥室/浴室/車位/面積
頁面顯示格式: `2 2 1 1(1) 600-699 sqft`
```html
<!-- 結構化數據列表 -->
<li><strong>MLS®#</strong> C12654644</li>
<li><strong>類型</strong> 公寓</li>
<li><strong>風格</strong> 共管公寓</li>
<li><strong>房齡</strong> New</li>
<li><strong>使用面積</strong> 600-699</li>
<li><strong>車位</strong> 1 Total Parking Spaces</li>
```
- **CSS 選擇器**: `li:contains("使用面積")`, `li:contains("車位")`

#### 房屋類型
```html
<li><strong>類型</strong> 公寓</li>
<li><strong>風格</strong> 共管公寓</li>
```
- **值**: 公寓, 獨立屋, 半獨立屋, 鎮屋 等

#### 描述/詳細說明
```html
<div class="description">
Plaza On Yonge, the newest addition to North York's vibrant Yonge & Finch community...
</div>
```
- **CSS 選擇器**: `.description`, `div:contains("詳細介紹")`

#### 經紀人信息
```html
<div class="agent-info">
    <span>Irene Li</span>
    <span>4168541538</span>
    <span>ireneli200912@gmail.com</span>
    <span>Homelife Landmark Realty Inc. Brokerage</span>
</div>
```
- **經紀公司**: `<li><strong>經紀公司</strong> HOMELIFE LANDMARK REALTY INC.</li>`

#### 圖片 URLs
```html
<img src="https://house.51img.ca/newhome/...">
<!-- 或使用 data-src 延遲加載 -->
<img data-src="https://...">
```
- **CSS 選擇器**: `img[src*="house.51img.ca"]`, `img[data-src]`

#### MLS 號碼
```html
<li><strong>MLS®#</strong> C12654644</li>
```
- **CSS 選擇器**: `li:contains("MLS")`

---

### 租房詳情頁面（用戶發布）

#### 物業類型/房間
```html
物業類型： 半獨立屋
房間情況： 1房
車       位： 無車位
廚衛情況： 未提供
所在樓層： 3層
使用面積： 未提供
```

#### 價格
```html
<span>$680 /月</span>
```

#### 聯繫人
```html
<li><strong>聯 系 人：</strong> Judy</li>
<li><strong>電子郵件：</strong> 未提供</li>
<li><strong>微信號：</strong> 未提供</li>
```

#### 房源特色
```html
<div class="features">
配套家具
有線電視
高速上網
洗衣機/房
冷暖空調
</div>
```

#### 出租對象/租客要求
```html
<div class="tenant-requirements">
學生
單身女性
不吸煙
</div>
```

---

## 3. BeautifulSoup 提取代碼建議

```python
from bs4 import BeautifulSoup
import re
from typing import Optional, Dict, List

class House51Scraper:
    """house.51.ca 房屋詳情頁面解析器"""
    
    def parse_mls_detail(self, html: str, url: str) -> Optional[Dict]:
        """解析 MLS 詳情頁面"""
        soup = BeautifulSoup(html, "lxml")
        data = {}
        
        # 1. 提取 MLS 號碼
        mls_elem = soup.find(string=re.compile(r'MLS.*#'))
        if mls_elem:
            parent = mls_elem.find_parent('li')
            if parent:
                mls_text = parent.get_text()
                mls_match = re.search(r'([A-Z]\d+)', mls_text)
                if mls_match:
                    data['listing_id'] = mls_match.group(1)
        
        # 2. 提取標題/地址
        # 方法1: h3 標題
        title_elem = soup.find('h3')
        if title_elem:
            data['title'] = title_elem.get_text(strip=True)
        
        # 方法2: 從地址信息提取
        address_match = re.search(r'(\d+.*?(?:Street|Ave|Road|Drive|Blvd).*?(?:Ontario|ON)\s*[A-Z]\d[A-Z]\s*\d[A-Z]\d)', 
                                  soup.get_text(), re.I)
        if address_match:
            data['address'] = address_match.group(1)
        
        # 3. 提取價格
        price_text = soup.find(string=re.compile(r'\$\s*[\d,]+'))
        if price_text:
            price_match = re.search(r'\$\s*([\d,]+)', price_text)
            if price_match:
                price_str = price_match.group(1).replace(',', '')
                data['price'] = float(price_str)
        
        # 判斷出售/出租
        page_text = soup.get_text().lower()
        if '出租' in page_text or 'rent' in page_text or '/月' in page_text:
            data['listing_type'] = '出租'
            data['price_unit'] = 'CAD/月'
        else:
            data['listing_type'] = '出售'
            data['price_unit'] = 'CAD'
        
        # 4. 提取房屋詳情（從列表項）
        data.update(self._extract_property_details(soup))
        
        # 5. 提取描述
        desc_elem = soup.find(class_=re.compile(r'description|content', re.I))
        if desc_elem:
            data['description'] = desc_elem.get_text(strip=True)[:2000]
        else:
            # 尋找 "房源描述" 區塊
            desc_section = soup.find(string=re.compile(r'房源描述'))
            if desc_section:
                parent = desc_section.find_parent('div')
                if parent:
                    data['description'] = parent.get_text(strip=True)[:2000]
        
        # 6. 提取經紀人信息
        data.update(self._extract_agent_info(soup))
        
        # 7. 提取圖片
        data['image_urls'] = self._extract_images(soup)
        
        # 8. 提取配套設施
        data['amenities'] = self._extract_amenities(soup)
        
        return data
    
    def _extract_property_details(self, soup: BeautifulSoup) -> Dict:
        """提取房屋詳細信息"""
        details = {}
        text = soup.get_text()
        
        # 房屋類型
        type_patterns = [
            (r'類型[：:]\s*(\S+)', 'property_type'),
            (r'風格[：:]\s*(\S+)', 'style'),
        ]
        for pattern, key in type_patterns:
            match = re.search(pattern, text)
            if match:
                details[key] = match.group(1)
        
        # 面積
        sqft_match = re.search(r'使用面積[：:]?\s*(\d+[-–]\d+|\d+)', text)
        if sqft_match:
            details['sqft'] = sqft_match.group(1)
        
        # 臥室
        bed_patterns = [
            r'(\d+)\+?(\d+)?\s*(?:臥|卧|bedroom|bed|房)',
            r'(\d+)\s*(?:br|BR)',
        ]
        for pattern in bed_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                details['bedrooms'] = match.group(0).strip()
                break
        
        # 浴室
        bath_match = re.search(r'(\d+)\s*(?:浴|bathroom|bath|wr|WR)', text, re.I)
        if bath_match:
            details['bathrooms'] = bath_match.group(1)
        
        # 車位
        parking_match = re.search(r'車位[：:]?\s*(\d+|無車位)', text)
        if parking_match:
            details['parking'] = parking_match.group(1)
        else:
            parking_match = re.search(r'(\d+)\s*(?:Total\s*)?Parking', text, re.I)
            if parking_match:
                details['parking'] = parking_match.group(1)
        
        # 樓層
        floor_match = re.search(r'所在樓層[：:]?\s*(\d+)層', text)
        if floor_match:
            details['floor'] = floor_match.group(1)
        
        # 房齡
        age_match = re.search(r'房齡[：:]?\s*(\S+)', text)
        if age_match:
            details['building_age'] = age_match.group(1)
        
        # 朝向
        facing_match = re.search(r'朝向[：:]?\s*(\S+)', text)
        if facing_match:
            details['facing'] = facing_match.group(1)
        
        # 地下室
        basement_match = re.search(r'地下室[：:]?\s*(\S+)', text)
        if basement_match:
            details['basement'] = basement_match.group(1)
        
        # 供暖/空調
        heating_match = re.search(r'供暖類型[：:]?\s*(\S+)', text)
        if heating_match:
            details['heating'] = heating_match.group(1)
        
        ac_match = re.search(r'空調類型[：:]?\s*(\S+)', text)
        if ac_match:
            details['air_conditioning'] = ac_match.group(1)
        
        return details
    
    def _extract_agent_info(self, soup: BeautifulSoup) -> Dict:
        """提取經紀人信息"""
        agent_data = {}
        text = soup.get_text()
        
        # 經紀人姓名
        agent_patterns = [
            r'聯\s*系\s*人[：:]\s*(\S+)',
            r'經紀[：:]\s*(\S+)',
            r'Broker[：:]?\s*(\S+)',
        ]
        for pattern in agent_patterns:
            match = re.search(pattern, text)
            if match:
                agent_data['agent_name'] = match.group(1)
                break
        
        # 電話號碼
        phone_patterns = [
            r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
            r'(\d{10})',
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                agent_data['agent_phone'] = match.group(1)
                break
        
        # 經紀公司
        company_match = re.search(r'經紀公司[：:]?\s*([^\n]+)', text)
        if company_match:
            agent_data['agent_company'] = company_match.group(1).strip()
        else:
            # 嘗試其他模式
            brokerage_match = re.search(r'([\w\s]+(?:Realty|Brokerage|Real Estate)[\w\s]*(?:Inc\.?)?)', 
                                        text, re.I)
            if brokerage_match:
                agent_data['agent_company'] = brokerage_match.group(1).strip()
        
        # 郵箱
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            agent_data['agent_email'] = email_match.group(0)
        
        return agent_data
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """提取圖片 URL"""
        images = []
        
        # 查找所有圖片
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if not src:
                continue
            
            # 過濾掉 logo、icon 等
            skip_keywords = ['logo', 'icon', 'avatar', 'button', 'banner', 
                           'loading', 'placeholder', 'blank']
            if any(kw in src.lower() for kw in skip_keywords):
                continue
            
            # 處理相對路徑
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = 'https://house.51.ca' + src
            
            # 只保留有效的 http URL
            if src.startswith('http'):
                images.append(src)
        
        # 去重並限制數量
        seen = set()
        unique_images = []
        for img in images:
            if img not in seen:
                seen.add(img)
                unique_images.append(img)
        
        return unique_images[:15]
    
    def _extract_amenities(self, soup: BeautifulSoup) -> List[str]:
        """提取設施和標籤"""
        amenities = []
        text = soup.get_text()
        
        # 配套設施標籤
        facility_tags = [
            '華人超市', '华人超市', 'Costco', '近地鐵', '近地铁',
            'Daycare', '近大學', '近大学', 'GoTrain', '名校',
            '配套家具', '有線電視', '高速上網', '洗衣機',
            '冷暖空調', 'Central Air', 'Elevator', 'Guest Suites',
            'Media Room', 'Outdoor Pool', 'Fitness', 'Party Room',
            '包水', '包電', '包網', '獨廚', '獨厕',
        ]
        
        for tag in facility_tags:
            if tag.lower() in text.lower():
                amenities.append(tag)
        
        # 從配套設施字段提取
        facilities_match = re.search(r'配套設施[：:]\s*([^\n]+)', text)
        if facilities_match:
            items = facilities_match.group(1).split(',')
            amenities.extend([item.strip() for item in items])
        
        return list(set(amenities))
    
    def parse_rental_detail(self, html: str, url: str) -> Optional[Dict]:
        """解析租房詳情頁面（用戶發布）"""
        soup = BeautifulSoup(html, "lxml")
        data = {}
        text = soup.get_text()
        
        # 從 URL 提取 ID
        url_match = re.search(r'/(\d+)(?:\?|$)', url)
        if url_match:
            data['listing_id'] = url_match.group(1)
        
        # 標題
        title_elem = soup.find('h2') or soup.find('h3')
        if title_elem:
            data['title'] = title_elem.get_text(strip=True)
        
        # 價格
        price_match = re.search(r'\$([\d,]+)\s*/月', text)
        if price_match:
            data['price'] = float(price_match.group(1).replace(',', ''))
            data['price_unit'] = 'CAD/月'
            data['listing_type'] = '出租'
        elif '面議' in text:
            data['price'] = None
            data['price_note'] = '面議'
        
        # 物業類型
        type_match = re.search(r'物業類型[：:]\s*(\S+)', text)
        if type_match:
            data['property_type'] = type_match.group(1)
        
        # 房間
        room_match = re.search(r'房間情況[：:]\s*(\d+房)', text)
        if room_match:
            data['bedrooms'] = room_match.group(1)
        
        # 車位
        parking_match = re.search(r'車\s*位[：:]\s*(.+?)(?:\n|$)', text)
        if parking_match:
            data['parking'] = parking_match.group(1).strip()
        
        # 樓層
        floor_match = re.search(r'所在樓層[：:]\s*(\d+)層', text)
        if floor_match:
            data['floor'] = floor_match.group(1)
        
        # 聯繫人
        contact_match = re.search(r'聯\s*系\s*人[：:]\s*(\S+)', text)
        if contact_match:
            data['agent_name'] = contact_match.group(1)
        
        # 地址/位置
        location_match = re.search(r'(?:士嘉堡|北約克|萬錦|密西沙加|多倫多)[（(]([^)）]+)[)）]', text)
        if location_match:
            data['address'] = location_match.group(1)
        
        # 圖片
        data['image_urls'] = self._extract_images(soup)
        
        # 設施
        data['amenities'] = self._extract_amenities(soup)
        
        return data


# 使用範例
if __name__ == "__main__":
    import requests
    
    scraper = House51Scraper()
    
    # 測試 MLS 頁面
    url = "https://house.51.ca/rental/ontario/toronto/north-york/604800"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = scraper.parse_mls_detail(response.text, url)
        print("提取結果:")
        for key, value in data.items():
            print(f"  {key}: {value}")
```

---

## 4. 重要發現

### URL 格式變化
- **舊格式**: `https://house.51.ca/property/{MLS_ID}` - 現在返回 404
- **新格式**: `https://house.51.ca/rental/ontario/{city}/{area}/{listing_id}`

### MLS 數據來源
MLS 房源頁面實際上嵌入了來自 `realtorireneli.ca` 的經紀人頁面，包含完整的 MLS 數據。

### 動態加載
- MLS 列表頁面 (`/mls`) 使用 JavaScript 動態加載
- 需要使用 Selenium 或類似工具來獲取完整列表

### 數據字段對應

| 字段 | 中文標籤 | 英文標籤 |
|------|---------|---------|
| MLS ID | MLS®# | MLS# |
| 類型 | 類型 | Type |
| 風格 | 風格 | Style |
| 面積 | 使用面積 | sqft |
| 臥室 | 臥室/房 | bedroom/br |
| 浴室 | 浴室/浴 | bathroom/wr |
| 車位 | 車位 | Parking |
| 房齡 | 房齡 | Age |
| 朝向 | 朝向 | Facing |
| 地下室 | 地下室 | Basement |
| 供暖 | 供暖類型 | Heating |
| 空調 | 空調類型 | A/C |
| 經紀公司 | 經紀公司 | Brokerage |

---

## 5. 建議的爬蟲改進

1. **更新 URL 匹配模式**: 支持新的 `/rental/ontario/...` 格式
2. **添加 Selenium 支持**: 用於抓取動態加載的 MLS 列表
3. **增強數據提取**: 添加更多字段如房齡、朝向、地下室類型等
4. **處理嵌入頁面**: 識別並提取 realtorireneli.ca 嵌入內容中的數據
