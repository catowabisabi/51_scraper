"""
51.ca 工作爬蟲
爬取 www.51.ca/jobs 的工作職位
"""

import re
import json
from typing import List, Dict, Optional
from datetime import datetime

from bs4 import BeautifulSoup

from base_scraper import BaseScraper
from models import save_job_listing, add_url_to_queue


class JobsScraper(BaseScraper):
    """工作爬蟲"""
    
    SCRAPER_NAME = "jobs_scraper"
    BASE_URL = "https://www.51.ca/jobs"
    URL_TYPE = "jobs"
    
    # 工作類別
    JOB_CATEGORIES = {
        '工厂工人': '工廠工人',
        '办公文员': '辦公文員',
        '销售代理': '銷售代理',
        '店员招待': '店員招待',
        '专业技术': '專業技術',
        '其他类别': '其他類別',
        '其他体力工': '其他體力工',
    }
    
    def get_start_urls(self) -> List[str]:
        """獲取起始URL列表"""
        urls = [
            f"{self.BASE_URL}",                    # 首頁
            f"{self.BASE_URL}/job-posts",          # 全部職位
            f"{self.BASE_URL}/urgently-hiring",    # 雇主急聘
        ]
        return urls
    
    def is_list_page(self, url: str) -> bool:
        """判斷是否為列表頁面"""
        # 詳情頁包含 /job-posts/ + 數字ID
        if re.search(r'/job-posts/\d+', url):
            return False
        return True
    
    def parse_list_page(self, html: str, url: str) -> List[Dict]:
        """解析工作列表頁面"""
        soup = BeautifulSoup(html, "lxml")
        items = []
        
        # 查找工作連結
        # 工作URL格式: https://www.51.ca/jobs/job-posts/1172771
        job_links = soup.find_all('a', href=re.compile(r'/jobs/job-posts/\d+'))
        
        seen_urls = set()
        for link in job_links:
            href = link.get('href', '')
            if not href:
                continue
            
            # 構建完整URL
            if href.startswith('/'):
                job_url = f"https://www.51.ca{href}"
            elif href.startswith('http'):
                job_url = href
            else:
                continue
            
            # 清理URL
            job_url = job_url.split('?')[0]
            
            # 避免重複
            if job_url in seen_urls:
                continue
            seen_urls.add(job_url)
            
            # 提取標題
            title = self.extract_text(link)
            
            items.append({
                'url': job_url,
                'title': title
            })
        
        self.logger.info(f"列表頁面發現 {len(items)} 個職位")
        return items
    
    def parse_detail_page(self, html: str, url: str) -> Optional[Dict]:
        """解析工作詳情頁面"""
        soup = BeautifulSoup(html, "lxml")
        
        # 提取職位ID
        job_id = self.extract_id_from_url(url, r'/job-posts/(\d+)')
        if not job_id:
            self.logger.warning(f"無法提取職位ID: {url}")
            return None
        
        # 提取標題
        title = self._extract_title(soup)
        
        # 提取公司信息
        company_name, company_url = self._extract_company(soup)
        
        # 從 company_url 提取 merchant_id
        merchant_id = None
        if company_url:
            import re as regex
            match = regex.search(r'/merchants/(\d+)', company_url)
            if match:
                merchant_id = match.group(1)
        
        # 提取薪資
        salary, salary_unit = self._extract_salary(soup)
        
        # 提取工作地點
        location = self._extract_location(soup)
        
        # 提取工作類型
        job_type, work_period, shift = self._extract_job_type(soup)
        
        # 提取類別
        category = self._extract_category(soup)
        
        # 提取描述
        description = self._extract_description(soup, html)
        
        # 提取要求
        requirements = self._extract_requirements(soup)
        
        # 提取福利
        benefits = self._extract_benefits(soup)
        
        # 提取聯繫方式
        contact_info = self._extract_contact(soup)
        
        # 提取發布日期
        post_date = self._extract_post_date(soup)
        
        data = {
            'job_id': job_id,
            'url': url,
            'title': title,
            'company_name': company_name,
            'company_url': company_url,
            'merchant_id': merchant_id,
            'salary': salary,
            'salary_unit': salary_unit,
            'location': location,
            'job_type': job_type,
            'work_period': work_period,
            'shift': shift,
            'category': category,
            'description': description,
            'requirements': self.to_json(requirements),
            'benefits': self.to_json(benefits),
            'contact_info': contact_info,
            'post_date': post_date
        }
        
        self.logger.debug(f"解析職位: {job_id} - {title[:30] if title else 'N/A'}...")
        return data
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取標題"""
        # 方法1: 使用正確的 CSS 選擇器
        title_elem = soup.select_one('h1.overview-section .inner > strong')
        if title_elem:
            return self.clean_text(title_elem.get_text()).strip()
        
        # 方法2: 備用 - 查找 h1 內的 strong
        h1 = soup.find('h1', class_=re.compile(r'overview'))
        if h1:
            inner = h1.find(class_='inner')
            if inner:
                strong = inner.find('strong')
                if strong:
                    return self.clean_text(strong.get_text()).strip()
        
        # 方法3: 傳統方式
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            title = self.clean_text(self.extract_text(title_elem))
            # 移除網站名稱和多餘的按鈕文字
            title = re.sub(r'\s*[-|]\s*51.*$', '', title)
            # 移除價格後的收藏、電話等按鈕文字
            title = re.sub(r'(加元/[小时年時]+|面议).*$', r'\1', title)
            title = re.sub(r'收藏职位.*$', '', title)
            title = re.sub(r'拨打电话.*$', '', title)
            title = re.sub(r'发送邮件.*$', '', title)
            title = re.sub(r'查看电话.*$', '', title)
            return title.strip()
        return ""
    
    def _extract_company(self, soup: BeautifulSoup) -> tuple:
        """提取公司信息"""
        company_name = None
        company_url = None
        
        # 查找公司連結
        company_link = soup.find('a', href=re.compile(r'/merchants/\d+'))
        if company_link:
            company_name = self.extract_text(company_link)
            href = company_link.get('href', '')
            if href.startswith('/'):
                company_url = f"https://merchant.51.ca{href}"
            else:
                company_url = href
        
        return company_name, company_url
    
    def _extract_salary(self, soup: BeautifulSoup) -> tuple:
        """提取薪資"""
        salary = None
        salary_unit = None
        
        text = soup.get_text()
        
        # 匹配薪資格式
        # 格式: 18.00~22.50加元/小时, 面议, 38,400~60,000加元/年
        salary_patterns = [
            r'([\d,.]+~?[\d,.]*)加元/小[時时]',
            r'([\d,.]+~?[\d,.]*)加元/年',
            r'\$([\d,.]+~?[\d,.]*)/h',
            r'\$([\d,.]+~?[\d,.]*)',
            r'(面[议議])',
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, text)
            if match:
                salary = match.group(0)
                if '小時' in salary or '小时' in salary or '/h' in salary.lower():
                    salary_unit = '時薪'
                elif '年' in salary:
                    salary_unit = '年薪'
                elif '面' in salary:
                    salary_unit = '面議'
                break
        
        return salary, salary_unit
    
    def _extract_location(self, soup: BeautifulSoup) -> str:
        """提取工作地點"""
        text = soup.get_text()
        
        # 常見地點
        locations = ['士嘉堡', '北約克', '北约克', '萬錦', '万锦', '列治文山', 
                     '密西沙加', '多市中心', '多伦多', '多倫多', '大多地區', '大多地区',
                     'Scarborough', 'North York', 'Markham', 'Richmond Hill',
                     'Mississauga', 'Toronto', 'Etobicoke', 'Vaughan']
        
        for loc in locations:
            if loc in text:
                return loc
        
        return None
    
    def _extract_job_type(self, soup: BeautifulSoup) -> tuple:
        """提取工作類型"""
        text = soup.get_text()
        
        job_type = None
        work_period = None
        shift = None
        
        # 工作類型
        if '全职' in text or '全職' in text:
            job_type = '全職'
        elif '兼职' in text or '兼職' in text:
            job_type = '兼職'
        elif '全职/兼职' in text or '全職/兼職' in text:
            job_type = '全職/兼職'
        
        # 工作時長
        if '长期' in text or '長期' in text:
            work_period = '長期工'
        elif '短期' in text:
            work_period = '短期工'
        
        # 班次
        shifts = []
        if '白班' in text:
            shifts.append('白班')
        if '中班' in text:
            shifts.append('中班')
        if '夜班' in text:
            shifts.append('夜班')
        if shifts:
            shift = '/'.join(shifts)
        
        return job_type, work_period, shift
    
    def _extract_category(self, soup: BeautifulSoup) -> str:
        """提取類別"""
        text = soup.get_text()
        
        for cn_cat, tw_cat in self.JOB_CATEGORIES.items():
            if cn_cat in text:
                return tw_cat
        
        return '其他'
    
    def _extract_description(self, soup: BeautifulSoup, html: str) -> str:
        """提取描述"""
        # 排除不需要的內容
        exclude_texts = [
            '常用入口', '租房发布管理', '黄页发布管理', '工作发布管理',
            '集市发布管理', '汽车发布管理', '工具汇率', '用户中心',
            '修改密码', '修改邮箱', '修改昵称', '修改头像', '电话认证',
            '绑定电话', '帮助中心', '请谨慎以下行为', '如发现可疑信息',
        ]
        
        # 方法1: 使用 p.detail-intro-content 選擇器 (最準確)
        intro_elem = soup.select_one('p.detail-intro-content')
        if intro_elem:
            desc = intro_elem.get_text(separator='\n', strip=True)
            if desc and len(desc) > 10 and not any(ex in desc for ex in exclude_texts):
                return self.clean_text(desc)[:2000]
        
        # 方法2: 使用 class 模糊匹配
        intro_elem = soup.find(class_=re.compile(r'detail-intro-content'))
        if intro_elem:
            desc = intro_elem.get_text(separator='\n', strip=True)
            if desc and len(desc) > 10 and not any(ex in desc for ex in exclude_texts):
                return self.clean_text(desc)[:2000]
        
        # 方法3: 查找 .job-detail-section 內的內容
        detail_section = soup.select_one('.job-detail-section')
        if detail_section:
            # 移除不需要的元素
            for tag in detail_section.find_all(['script', 'style', 'nav', 'footer', 'aside']):
                tag.decompose()
            desc = detail_section.get_text(separator='\n', strip=True)
            # 移除「詳細介紹」標題
            desc = re.sub(r'^详细介绍\s*', '', desc)
            if desc and len(desc) > 20 and not any(ex in desc for ex in exclude_texts):
                return self.clean_text(desc)[:2000]
        
        # 方法4: 從頁面中找職位內容段落
        job_patterns = [
            r'([\u4e00-\u9fff]+(高薪聘|急聘|诚聘|招聘)[\s\S]{20,500}?(?:联系|电话|請|请|谢谢|薪资面议))',
            r'(工作(内容|职责|描述)[：:\s][\s\S]{20,500}?(?:联系|电话|請|请|谢谢))',
        ]
        for pattern in job_patterns:
            match = re.search(pattern, html)
            if match:
                # 清理 HTML 標籤
                desc = re.sub(r'<[^>]+>', ' ', match.group(1))
                desc = re.sub(r'\s+', ' ', desc)
                desc = self.clean_text(desc)
                if desc and not any(ex in desc for ex in exclude_texts):
                    return desc[:2000]
        
        return ""
    
    def _extract_requirements(self, soup: BeautifulSoup) -> List[str]:
        """提取要求"""
        requirements = []
        text = soup.get_text()
        
        # 常見要求
        req_keywords = [
            '需相关经验', '需相關經驗',
            '需相关证书', '需相關證書',
            '自备用车', '自備用車',
            '身体强壮', '身體強壯',
            '需要工作签证', '需要工作簽證',
            '英语', '英語',
            '国语', '國語',
            '粤语', '粵語',
        ]
        
        for req in req_keywords:
            if req in text:
                requirements.append(req)
        
        return requirements
    
    def _extract_benefits(self, soup: BeautifulSoup) -> List[str]:
        """提取福利"""
        benefits = []
        text = soup.get_text()
        
        # 常見福利
        benefit_keywords = [
            '可提供工作证明', '可提供工作證明',
            '欢迎学生', '歡迎學生',
            '免费工作餐', '免費工作餐',
            '有保险', '有保險',
            '有福利',
        ]
        
        for benefit in benefit_keywords:
            if benefit in text:
                benefits.append(benefit)
        
        return benefits
    
    def _extract_contact(self, soup: BeautifulSoup) -> str:
        """提取聯繫方式"""
        text = soup.get_text()
        
        # 電話
        phone_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', text)
        if phone_match:
            return phone_match.group(1)
        
        # Email
        email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
        if email_match:
            return email_match.group(0)
        
        return None
    
    def _extract_post_date(self, soup: BeautifulSoup) -> Optional[str]:
        """提取發布日期"""
        text = soup.get_text()
        
        # 相對時間
        time_patterns = [
            (r'(\d+)小時前', lambda m: (datetime.now() - __import__('datetime').timedelta(hours=int(m.group(1)))).strftime('%Y-%m-%d')),
            (r'(\d+)天前', lambda m: (datetime.now() - __import__('datetime').timedelta(days=int(m.group(1)))).strftime('%Y-%m-%d')),
            (r'(\d{4}-\d{2}-\d{2})', lambda m: m.group(1)),
        ]
        
        for pattern, converter in time_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return converter(match)
                except:
                    pass
        
        return None
    
    def save_item(self, data: Dict) -> bool:
        """保存工作職位"""
        return save_job_listing(data)
    
    def run_jobs_scraper(self, max_pages: int = 50):
        """運行工作爬蟲"""
        start_urls = self.get_start_urls()
        self.run(start_urls=start_urls, max_pages=max_pages)


def main():
    """主函數"""
    scraper = JobsScraper(headless=True)
    scraper.run_jobs_scraper(max_pages=30)


if __name__ == "__main__":
    main()
