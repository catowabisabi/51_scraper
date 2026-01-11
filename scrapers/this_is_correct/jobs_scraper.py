"""
51.ca 工作爬蟲 (Playwright + API)
結合 API 分頁和 Playwright 電話提取

用法:
    python -m scrapers.jobs_scraper --max-jobs 100
"""

import json
import re
import time
from typing import List, Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from playwright.sync_api import sync_playwright, Page, Browser

from .base import BaseScraper
from .models import get_connection


class JobsScraper(BaseScraper):
    """工作爬蟲"""
    
    SCRAPER_NAME = "jobs"
    BASE_URL = "https://www.51.ca/jobs"
    API_URL = "https://www.51.ca/jobs/api/job-posts"
    
    def __init__(self):
        super().__init__()
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self._playwright = None
    
    # 實現抽象方法
    def get_start_urls(self) -> List[str]:
        return [f"{self.BASE_URL}/job-posts"]
    
    def is_list_page(self, url: str) -> bool:
        return '/job-posts' in url and not re.search(r'/job-posts/\d+', url)
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        return []
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        return None
    
    def save_item(self, data: Dict) -> bool:
        """保存項目到資料庫 - 實現抽象方法"""
        return self.save_job(data)
    
    def _init_browser(self, headless: bool = True):
        """初始化瀏覽器"""
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=headless)
        self._page = self._browser.new_page()
        self._page.set_viewport_size({"width": 1280, "height": 800})
    
    def _close_browser(self):
        """關閉瀏覽器"""
        try:
            if self._browser:
                self._browser.close()
        except:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except:
            pass
    
    def _fetch_job_list_from_api(self, page: int = 1, per_page: int = 50) -> tuple:
        """從 API 獲取工作列表
        
        Returns:
            (jobs, pagination) - 工作列表和分頁信息
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': f'{self.BASE_URL}/job-posts',
        }
        
        url = f"{self.API_URL}?page={page}&perPage={per_page}"
        
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code != 200:
                self.logger.error(f"API 請求失敗: {resp.status_code}")
                return [], None
            
            data = resp.json()
            pagination = data.get('pagination', {})
            
            # 解析 HTML 數據
            html_data = data.get('data', {})
            html_content = html_data.get('html', '') if isinstance(html_data, dict) else html_data
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            jobs = []
            job_items = soup.select('.job-item')
            
            for item in job_items:
                try:
                    job = self._parse_job_item(item)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    self.logger.debug(f"解析工作項失敗: {e}")
            
            return jobs, pagination
            
        except Exception as e:
            self.logger.error(f"API 請求錯誤: {e}")
            return [], None
    
    def _parse_job_item(self, item) -> Optional[Dict]:
        """解析工作列表項"""
        try:
            # 找連結和 ID
            link = item.find('a', href=re.compile(r'/job-posts/\d+'))
            if not link:
                return None
            
            href = link.get('href', '')
            match = re.search(r'/job-posts/(\d+)', href)
            if not match:
                return None
            
            job_id = int(match.group(1))
            
            # 標題
            title_elem = item.find(['h3', 'h4', '.title', 'a'])
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            # 薪資
            salary_elem = item.find(class_=re.compile(r'salary|wage|pay'))
            salary = salary_elem.get_text(strip=True) if salary_elem else ''
            
            # 地點
            location_elem = item.find(class_=re.compile(r'location|area'))
            location = location_elem.get_text(strip=True) if location_elem else ''
            
            # 標籤
            tags = []
            tag_elems = item.find_all(class_=re.compile(r'tag|label|badge'))
            for tag in tag_elems:
                tags.append(tag.get_text(strip=True))
            
            return {
                'id': job_id,
                'title': title,
                'url': f"https://www.51.ca{href}" if href.startswith('/') else href,
                'salary': salary,
                'location': location,
                'tags': tags,
            }
            
        except Exception as e:
            self.logger.debug(f"解析失敗: {e}")
            return None
    
    def _fetch_job_detail(self, job_id: int) -> Optional[Dict]:
        """獲取工作詳情（含電話）"""
        try:
            url = f"{self.BASE_URL}/job-posts/{job_id}"
            self._page.goto(url, wait_until='networkidle', timeout=15000)
            time.sleep(0.5)
            
            detail = {}
            
            # 獲取電話
            tel_links = self._page.locator('a[href^="tel:"]')
            if tel_links.count() > 0:
                href = tel_links.first.get_attribute('href')
                detail['phone'] = href.replace('tel:', '')
            else:
                # 點擊查看電話按鈕
                phone_btn = self._page.locator('button:has-text("查看电话")')
                if phone_btn.count() > 0:
                    phone_btn.first.click()
                    time.sleep(0.8)
                    
                    # 確認彈窗
                    confirm_btn = self._page.locator('button:has-text("知道了")')
                    if confirm_btn.count() > 0:
                        confirm_btn.first.click()
                        time.sleep(0.3)
                    
                    # 再次找電話
                    tel_links = self._page.locator('a[href^="tel:"]')
                    if tel_links.count() > 0:
                        href = tel_links.first.get_attribute('href')
                        detail['phone'] = href.replace('tel:', '')
            
            # 從 window._DEP_DATA 獲取更多信息（Jobs 頁面用這個，不是 __NEXT_DATA__）
            dep_data = self._page.evaluate('() => window._DEP_DATA')
            
            if dep_data:
                detail['raw_data'] = dep_data
                
                # 提取字段
                detail['title'] = dep_data.get('title', '')
                
                # digest 包含更多信息
                digest = dep_data.get('digest', {})
                if digest:
                    detail['location'] = digest.get('workLocation', '')
                    detail['address'] = digest.get('workPlaceAddress', '')
                    detail['publisher'] = digest.get('employerName', '') or digest.get('publisher', {}).get('name', '')
                    detail['tags'] = digest.get('tags', [])
                    detail['is_recommended'] = digest.get('isPromote', False)
                
                # 分類需要從頁面提取
                category_elem = self._page.locator('a[href*="jobCategoryId="]')
                if category_elem.count() > 0:
                    detail['category'] = category_elem.first.inner_text()
            
            # 從頁面提取詳細描述 (第二個 .job-detail-section 包含 "詳細介紹")
            detail_sections = self._page.locator('.job-detail-section')
            if detail_sections.count() >= 2:
                # 第二個 section 包含詳細介紹
                content_section = detail_sections.nth(1).inner_text()
                # 移除 "詳細介紹" 標題
                if content_section.startswith('详细介绍'):
                    content_section = content_section[4:].strip()
                # 移除末尾的發布時間等
                if '发布时间：' in content_section:
                    content_section = content_section.split('发布时间：')[0].strip()
                detail['content'] = content_section
            
            return detail
            
        except Exception as e:
            self.logger.debug(f"獲取詳情失敗 {job_id}: {e}")
            return None
    
    def save_job(self, job: Dict) -> bool:
        """保存工作到數據庫"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # 創建表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    content TEXT,
                    salary TEXT,
                    location TEXT,
                    address TEXT,
                    category TEXT,
                    publisher TEXT,
                    phone TEXT,
                    url TEXT,
                    tags TEXT,
                    view_count INTEGER DEFAULT 0,
                    is_recommended BOOLEAN DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    scraped_at TEXT,
                    raw_data TEXT
                )
            ''')
            
            # 插入或更新
            cursor.execute('''
                INSERT OR REPLACE INTO jobs 
                (id, title, content, salary, location, address, category, publisher, 
                 phone, url, tags, view_count, is_recommended, 
                 created_at, updated_at, scraped_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job.get('id'),
                job.get('title', ''),
                job.get('content', ''),
                job.get('salary', ''),
                job.get('location', ''),
                job.get('address', ''),
                job.get('category', ''),
                job.get('publisher', ''),
                job.get('phone', ''),
                job.get('url', ''),
                json.dumps(job.get('tags', []), ensure_ascii=False),
                job.get('view_count', 0),
                1 if job.get('is_recommended') else 0,
                job.get('created_at', ''),
                job.get('updated_at', ''),
                datetime.now().isoformat(),
                json.dumps(job.get('raw_data', {}), ensure_ascii=False) if job.get('raw_data') else ''
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"保存失敗 {job.get('id')}: {e}")
            return False
    
    def run(self, max_jobs: int = 100, fetch_details: bool = True, 
            headless: bool = True, per_page: int = 50):
        """
        運行爬蟲
        
        Args:
            max_jobs: 最大抓取數量
            fetch_details: 是否獲取詳情（含電話）
            headless: 是否無頭模式
            per_page: 每頁數量
        """
        self.logger.info(f"開始爬取工作，最大數量: {max_jobs}")
        
        try:
            if fetch_details:
                self._init_browser(headless=headless)
            
            all_jobs = []
            page = 1
            
            while len(all_jobs) < max_jobs:
                self.logger.info(f"獲取第 {page} 頁...")
                
                jobs, pagination = self._fetch_job_list_from_api(page=page, per_page=per_page)
                
                if not jobs:
                    self.logger.info("沒有更多數據")
                    break
                
                for job in jobs:
                    if len(all_jobs) >= max_jobs:
                        break
                    
                    # 獲取詳情
                    if fetch_details:
                        self.logger.info(f"  獲取詳情: {job['id']}")
                        detail = self._fetch_job_detail(job['id'])
                        if detail:
                            job.update(detail)
                        time.sleep(0.3)
                    
                    # 保存
                    if self.save_job(job):
                        all_jobs.append(job)
                        self.logger.debug(f"  保存成功: {job['id']}")
                
                # 檢查是否有下一頁
                if pagination:
                    last_page = pagination.get('lastPage', 1)
                    if page >= last_page:
                        self.logger.info("已到最後一頁")
                        break
                
                page += 1
            
            self.logger.info(f"完成! 共保存 {len(all_jobs)} 個工作")
            
            # 統計電話
            with_phone = sum(1 for j in all_jobs if j.get('phone'))
            self.logger.info(f"有電話: {with_phone}/{len(all_jobs)} ({with_phone*100//len(all_jobs) if all_jobs else 0}%)")
            
            return all_jobs
            
        finally:
            if fetch_details:
                self._close_browser()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='51.ca 工作爬蟲')
    parser.add_argument('--max-jobs', type=int, default=100, help='最大抓取數量')
    parser.add_argument('--no-details', action='store_true', help='不獲取詳情')
    parser.add_argument('--no-headless', action='store_true', help='顯示瀏覽器')
    parser.add_argument('--per-page', type=int, default=50, help='每頁數量')
    
    args = parser.parse_args()
    
    scraper = JobsScraper()
    scraper.run(
        max_jobs=args.max_jobs,
        fetch_details=not args.no_details,
        headless=not args.no_headless,
        per_page=args.per_page
    )


if __name__ == '__main__':
    main()
