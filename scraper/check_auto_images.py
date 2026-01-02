"""
汽車圖片死鏈檢查與修復
驗證 auto_listings 中的圖片 URL 有效性
"""
import sqlite3
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

DB_PATH = '../data/51ca.db'

def check_url(url: str, timeout: int = 5) -> tuple:
    """檢查 URL 是否有效"""
    try:
        # 只發送 HEAD 請求以節省帶寬
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return (url, response.status_code, response.status_code == 200)
    except requests.exceptions.Timeout:
        return (url, 0, False)
    except requests.exceptions.RequestException as e:
        return (url, -1, False)

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print('=== 汽車圖片死鏈檢查 ===')
    
    # 獲取所有汽車列表的圖片
    c.execute('SELECT listing_id, title, image_urls FROM auto_listings WHERE image_urls IS NOT NULL')
    rows = c.fetchall()
    
    print(f'總汽車列表: {len(rows)}')
    
    # 收集所有圖片 URL
    all_images = []
    for listing_id, title, image_urls_json in rows:
        try:
            images = json.loads(image_urls_json) if image_urls_json else []
            for img in images:
                all_images.append((listing_id, title[:30], img))
        except json.JSONDecodeError:
            print(f'  ⚠ 無法解析圖片 JSON: listing_id={listing_id}')
    
    print(f'總圖片數: {len(all_images)}')
    
    if not all_images:
        print('沒有圖片需要檢查')
        conn.close()
        return
    
    # 抽樣檢查 (如果圖片太多，只檢查前 50 個)
    sample_size = min(50, len(all_images))
    sample = all_images[:sample_size]
    
    print(f'\n檢查 {sample_size} 張圖片...')
    
    dead_links = []
    valid_count = 0
    
    # 並行檢查
    urls_to_check = [img[2] for img in sample]
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_url, url): url for url in urls_to_check}
        
        for future in as_completed(futures):
            url, status, is_valid = future.result()
            if is_valid:
                valid_count += 1
            else:
                # 找到對應的 listing
                for lid, title, img_url in sample:
                    if img_url == url:
                        dead_links.append((lid, title, url, status))
                        break
    
    print(f'\n檢查結果:')
    print(f'  有效圖片: {valid_count}/{sample_size}')
    print(f'  死鏈圖片: {len(dead_links)}/{sample_size}')
    
    if dead_links:
        print(f'\n死鏈詳情:')
        for lid, title, url, status in dead_links[:10]:
            print(f'  - [{status}] {title}: {url[:60]}...')
        
        # 統計域名問題
        print('\n死鏈域名統計:')
        domain_counts = {}
        for _, _, url, _ in dead_links:
            domain = urlparse(url).netloc
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
            print(f'  {domain}: {count}')
    
    # 分析圖片 URL 格式
    print('\n=== 圖片 URL 格式分析 ===')
    domains = {}
    for _, _, url in all_images:
        domain = urlparse(url).netloc
        domains[domain] = domains.get(domain, 0) + 1
    
    for domain, count in sorted(domains.items(), key=lambda x: -x[1])[:5]:
        print(f'  {domain}: {count} 張')
    
    conn.close()
    print('\n檢查完成!')

if __name__ == '__main__':
    main()
