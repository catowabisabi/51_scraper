"""
51.ca 工作 API 測試 - 解析 HTML API
"""

import json
import re
import requests
from bs4 import BeautifulSoup


def test_html_api():
    """測試返回 HTML 的 API"""
    print("=== 測試 Jobs HTML API ===\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.51.ca/jobs/job-posts',
    }
    
    # 獲取第一頁
    url = "https://www.51.ca/jobs/api/job-posts?page=1&perPage=50"
    print(f"GET {url}")
    
    resp = requests.get(url, headers=headers)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        
        # 分頁信息
        pagination = data.get('pagination', {})
        print(f"\n分頁信息:")
        print(f"  總數: {pagination.get('total')}")
        print(f"  每頁: {pagination.get('perPage')}")
        print(f"  當前頁: {pagination.get('page')}")
        print(f"  總頁數: {pagination.get('lastPage')}")
        
        # 解析 HTML
        html_data = data.get('data', {})
        if isinstance(html_data, dict):
            html_content = html_data.get('html', '')
        else:
            html_content = html_data
        
        print(f"\nHTML 長度: {len(html_content)}")
        
        # 保存原始 HTML
        with open('testing/jobs_api_html.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("已保存 HTML 到 testing/jobs_api_html.html")
        
        # 用 BeautifulSoup 解析
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 找工作列表項
        job_items = soup.select('li .job-item, .job-item, li[class*="job"]')
        print(f"\n找到 {len(job_items)} 個工作項")
        
        # 嘗試其他選擇器
        if len(job_items) == 0:
            all_li = soup.find_all('li')
            print(f"找到 {len(all_li)} 個 li 元素")
            if all_li:
                job_items = all_li
        
        # 找連結
        job_links = soup.find_all('a', href=re.compile(r'/jobs/job-posts/\d+'))
        print(f"找到 {len(job_links)} 個工作連結")
        
        jobs = []
        
        for link in job_links[:10]:
            href = link.get('href', '')
            # 提取 ID
            match = re.search(r'/job-posts/(\d+)', href)
            if match:
                job_id = match.group(1)
                
                # 找標題
                title = link.get_text(strip=True)
                if not title:
                    title_elem = link.find(['h3', 'h4', 'span', 'div'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                
                jobs.append({
                    'id': job_id,
                    'url': f"https://www.51.ca{href}" if href.startswith('/') else href,
                    'title': title[:50] if title else ''
                })
        
        print(f"\n解析到 {len(jobs)} 個工作:")
        for job in jobs[:5]:
            print(f"  ID: {job['id']}, 標題: {job['title'][:30]}")
        
        # 保存解析結果
        with open('testing/jobs_parsed.json', 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        print(f"\n已保存到 testing/jobs_parsed.json")
        
        return pagination, jobs


def test_pagination():
    """測試分頁"""
    print("\n\n=== 測試分頁 ===\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.51.ca/jobs/job-posts',
    }
    
    all_ids = set()
    
    for page in range(1, 4):
        url = f"https://www.51.ca/jobs/api/job-posts?page={page}&perPage=20"
        print(f"Page {page}: {url}")
        
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            html_data = data.get('data', {})
            html_content = html_data.get('html', '') if isinstance(html_data, dict) else html_data
            
            soup = BeautifulSoup(html_content, 'html.parser')
            links = soup.find_all('a', href=re.compile(r'/job-posts/(\d+)'))
            
            page_ids = []
            for link in links:
                match = re.search(r'/job-posts/(\d+)', link.get('href', ''))
                if match:
                    job_id = match.group(1)
                    page_ids.append(job_id)
                    all_ids.add(job_id)
            
            print(f"  找到 {len(page_ids)} 個工作, 第一個: {page_ids[0] if page_ids else 'N/A'}")
    
    print(f"\n共收集 {len(all_ids)} 個不重複 ID")
    print("✓ 分頁有效!" if len(all_ids) > 20 else "✗ 分頁無效")


if __name__ == '__main__':
    test_html_api()
    test_pagination()
