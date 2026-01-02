"""
51.ca 商家爬蟲
爬取 merchant.51.ca 的商家資訊
"""

import re
import json
from typing import List, Dict, Optional
from datetime import datetime

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from base_scraper import BaseScraper
from models import get_connection, save_merchant


class MerchantScraper(BaseScraper):
    """商家爬蟲 - 爬取 merchant.51.ca"""
    
    SCRAPER_NAME = "merchant_scraper"
    BASE_URL = "https://merchant.51.ca"
    URL_TYPE = "merchant"
    
    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.merchant_ids = set()
    
    def get_start_urls(self) -> List[str]:
        """獲取起始URL - 從首頁收集商家ID"""
        return [f"{self.BASE_URL}/"]
    
    def discover_merchant_ids(self) -> List[str]:
        """從首頁發現所有商家ID"""
        self.logger.info("開始從首頁收集商家ID...")
        
        html = self.fetch_page(f"{self.BASE_URL}/", wait_time=3.0)
        if not html:
            return []
        
        soup = BeautifulSoup(html, "lxml")
        
        # 找所有商家連結
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            match = re.search(r'/merchants/(\d+)', href)
            if match:
                self.merchant_ids.add(match.group(1))
        
        self.logger.info(f"從首頁發現 {len(self.merchant_ids)} 個商家ID")
        return list(self.merchant_ids)
    
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面"""
        return url == f"{self.BASE_URL}/" or url.endswith('/merchants')
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """解析列表頁面 - 提取商家連結"""
        soup = BeautifulSoup(html, "lxml")
        items = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            match = re.search(r'/merchants/(\d+)', href)
            if match:
                merchant_id = match.group(1)
                items.append({
                    'merchant_id': merchant_id,
                    'url': f"{self.BASE_URL}/merchants/{merchant_id}"
                })
        
        return items
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """解析商家詳情頁面"""
        soup = BeautifulSoup(html, "lxml")
        
        # 提取商家ID
        merchant_id = self.extract_id_from_url(url, r'/merchants/(\d+)')
        if not merchant_id:
            return None
        
        data = {
            'merchant_id': merchant_id,
            'url': url,
        }
        
        # 1. 商家名稱 - 從 .business-page__header__title 提取
        name_elem = soup.select_one('.business-page__header__title')
        if name_elem:
            full_name = name_elem.get_text(strip=True)
            # 分離中英文名稱
            # 例如: "大统华超级市场T&T Supermarket"
            parts = re.split(r'(?<=[一-龥])(?=[A-Za-z])', full_name, 1)
            data['name'] = parts[0].strip() if parts else full_name
            data['english_name'] = parts[1].strip() if len(parts) > 1 else ''
        
        # 2. Logo URL - 從 merchant-logo 圖片
        logo_elem = soup.find('img', src=re.compile(r'merchant-logo/[^/]+\.(jpg|jpeg|png)', re.I))
        if logo_elem:
            data['logo_url'] = logo_elem.get('src', '')
        
        # 3. 瀏覽數
        view_elem = soup.find(string=re.compile(r'(\d+)\s*人看过'))
        if view_elem:
            match = re.search(r'(\d+)', view_elem)
            if match:
                data['review_count'] = int(match.group(1))  # 用 review_count 存瀏覽數
        
        # 4. 公司介紹 - 找「公司介绍」section，只提取內容，跳過標題
        for sec in soup.find_all(['section', 'div'], recursive=True):
            heading = sec.find(['h2', 'h3'], string=re.compile('公司介[绍紹]'))
            if heading:
                # 找描述內容 - 尋找緊跟標題的 p 或 div
                content_parts = []
                for sibling in heading.find_next_siblings():
                    text = sibling.get_text(strip=True)
                    # 遇到下一個 section 標題就停止
                    if sibling.name in ['h2', 'h3'] or '联系我们' in text or '聯繫我們' in text:
                        break
                    if text:
                        content_parts.append(text)
                
                if content_parts:
                    description = ' '.join(content_parts)
                else:
                    # Fallback: 直接提取，但過濾冗餘內容
                    all_text = sec.get_text(separator=' ', strip=True)
                    all_text = re.sub(r'公司介[绍紹]', '', all_text)
                    all_text = re.sub(r'最新[动動][态態]\s*更多[动動][态態]', '', all_text)
                    description = all_text.strip()
                
                if description and len(description) > 10:
                    data['description'] = description[:2000]
                break
        
        # 5. 從「聯繫我們」section 提取聯繫資訊
        contact_section = None
        for sec in soup.find_all(['section', 'div'], recursive=True):
            heading = sec.find(['h2', 'h3'], string=re.compile('联系我们|聯繫我們'))
            if heading:
                contact_section = sec
                break
        
        if contact_section:
            # 電話 - 從 tel: 連結提取
            phones = []
            for tel in contact_section.find_all('a', href=re.compile(r'^tel:')):
                phone = tel.get('href', '').replace('tel:', '').replace('-', '')
                if phone and phone not in phones:
                    phones.append(phone)
            if phones:
                data['phone'] = ', '.join(phones)
            
            # 郵箱 - 從 mailto: 連結提取
            emails = []
            for mail in contact_section.find_all('a', href=re.compile(r'^mailto:')):
                email = mail.get('href', '').replace('mailto:', '')
                if email and email not in emails:
                    emails.append(email)
            if emails:
                data['website'] = ', '.join(emails)  # 暫用 website 存郵箱
            
            # 地址 - 從 Google Maps 連結提取 (最精準)
            maps_link = contact_section.find('a', href=re.compile(r'google\.com/maps'))
            if maps_link:
                maps_url = maps_link.get('href', '')
                addr_match = re.search(r'query=([^&]+)', maps_url)
                if addr_match:
                    from urllib.parse import unquote
                    addr = unquote(addr_match.group(1).replace('+', ' '))
                    if addr and len(addr) > 5:
                        data['address'] = addr
            
            # 如果沒有從 Google Maps 拿到地址，嘗試從文字匹配
            if 'address' not in data:
                info_text = contact_section.get_text()
                # 移除「查看路線」等干擾文字
                info_text = re.sub(r'查看路[线線]', '', info_text)
                addr_patterns = [
                    r'[\w\s\d]+,\s*[\w\s]+,\s*(?:ON|BC|AB|QC|MB|SK|NS|NB)\s*[A-Z]\d[A-Z]\s*\d[A-Z]\d',
                    r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Way|Court|Ct|Circle|Cir|Lane|Ln)[,\s]+[\w\s]+,\s*(?:ON|BC|AB|QC)',
                ]
                for pattern in addr_patterns:
                    addr_match = re.search(pattern, info_text, re.I)
                    if addr_match:
                        addr = addr_match.group().strip().lstrip(',').strip()
                        if len(addr) > 5:
                            data['address'] = addr
                            break
        
        # 6. 辦公環境圖片
        images = []
        for img in soup.find_all('img', src=re.compile(r'merchant-photos/|merchant-moment-photos/')):
            src = img.get('src', '')
            if src and src not in images:
                images.append(src)
        if images:
            data['image_urls'] = json.dumps(images[:10], ensure_ascii=False)  # 最多10張
        
        # 7. 分類 - 從多個來源嘗試提取
        category = None
        
        # 方法1: 從黃頁連結提取 /service/categories/xxx/
        for link in soup.find_all('a', href=re.compile(r'/service/categories/([^/]+)/')):
            href = link.get('href', '')
            cat_match = re.search(r'/categories/([^/]+)/', href)
            if cat_match:
                category = cat_match.group(1)
                break
        
        # 方法2: 從頁面 meta 或其他結構化數據
        if not category:
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    ld_data = json.loads(script.string or '{}')
                    if isinstance(ld_data, dict):
                        cat = ld_data.get('category') or ld_data.get('@type')
                        if cat and cat != 'Organization':
                            category = cat
                            break
                except:
                    pass
        
        # 方法3: 從頁面導航或麵包屑提取
        if not category:
            breadcrumb = soup.select_one('.breadcrumb, nav[aria-label="breadcrumb"]')
            if breadcrumb:
                links = breadcrumb.find_all('a')
                for link in links:
                    text = link.get_text(strip=True)
                    if text and text not in ['首页', '商家', 'Home', '51商家']:
                        category = text
                        break
        
        if category:
            data['category'] = category
        
        self.logger.info(f"解析商家: {data.get('name', merchant_id)}")
        return data
    
    def save_item(self, data: Dict) -> bool:
        """保存商家到資料庫"""
        try:
            success = save_merchant(data)
            if success:
                self.logger.info(f"保存商家: {data.get('name', data.get('merchant_id'))}")
            return success
        except Exception as e:
            self.logger.error(f"保存商家失敗: {e}")
            return False
    
    def run_all(self, max_merchants: int = 200):
        """爬取所有商家"""
        self.stats['start_time'] = datetime.now()
        self.logger.info("=" * 50)
        self.logger.info("開始爬取商家資訊...")
        
        try:
            self.start_browser()
            
            # 1. 從首頁收集商家ID
            merchant_ids = self.discover_merchant_ids()
            if not merchant_ids:
                self.logger.warning("沒有找到商家ID")
                return
            
            # 限制數量
            merchant_ids = merchant_ids[:max_merchants]
            self.logger.info(f"準備爬取 {len(merchant_ids)} 個商家")
            
            # 2. 逐個爬取商家詳情
            for i, merchant_id in enumerate(merchant_ids):
                url = f"{self.BASE_URL}/merchants/{merchant_id}"
                self.logger.info(f"[{i+1}/{len(merchant_ids)}] 爬取商家: {url}")
                
                html = self.fetch_page(url, wait_time=2.0)
                if not html:
                    continue
                
                data = self.parse_detail_page(html, url)
                if data:
                    self.save_item(data)
                
                # 避免請求過快
                import time
                time.sleep(0.5)
            
        except Exception as e:
            self.logger.error(f"爬取過程發生錯誤: {e}")
        finally:
            self.close_browser()
            self.stats['end_time'] = datetime.now()
            self._print_stats()
    
    def _print_stats(self):
        """打印統計"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        self.logger.info("=" * 50)
        self.logger.info("爬取完成!")
        self.logger.info(f"頁面數: {self.stats['pages_scraped']}")
        self.logger.info(f"保存項目: {self.stats['items_saved']}")
        self.logger.info(f"錯誤數: {self.stats['errors']}")
        self.logger.info(f"耗時: {duration:.1f} 秒")
        self.logger.info("=" * 50)


def main():
    """主函數"""
    from models import init_database
    
    # 初始化資料庫
    init_database()
    
    # 創建爬蟲並運行
    scraper = MerchantScraper(headless=True)
    scraper.run_all(max_merchants=200)
    
    # 顯示結果
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM service_merchants")
    count = cursor.fetchone()[0]
    conn.close()
    print(f"\n資料庫中共有 {count} 個商家")


if __name__ == "__main__":
    main()
