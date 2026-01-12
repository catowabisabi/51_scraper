"""
獲取更多汽車數據 - 直接使用現有的 auto_scraper
"""
import sys
import os

# 添加路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.auto_scraper import AutoScraper
from scrapers.models import get_connection

def fetch_more_autos():
    """獲取更多汽車"""
    print("=" * 50)
    print("獲取更多汽車數據")
    print("=" * 50)
    
    # 檢查當前數量
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM auto_listings")
    before = c.fetchone()[0]
    print(f"當前汽車數量: {before}")
    conn.close()
    
    # 運行爬蟲 - 多個頁面
    scraper = AutoScraper()
    
    # 擴展起始 URL
    urls = [
        "https://www.51.ca/autos/",
        "https://www.51.ca/autos/used-cars",
        "https://www.51.ca/autos/new-cars",
        "https://www.51.ca/autos/lease-cars",
    ]
    
    # 添加多個分頁
    for page in range(1, 51):
        urls.append(f"https://www.51.ca/autos/used-cars?page={page}")
        urls.append(f"https://www.51.ca/autos/new-cars?page={page}")
        urls.append(f"https://www.51.ca/autos/lease-cars?page={page}")
    
    # 設置起始 URL
    scraper.start_urls = urls
    
    # 運行
    try:
        scraper.run(start_urls=urls, max_pages=500)
        print(f"\n爬取完成")
    except Exception as e:
        print(f"爬蟲錯誤: {e}")
    
    # 檢查最終數量
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM auto_listings")
    after = c.fetchone()[0]
    print(f"\n汽車數量: {before} -> {after} (新增 {after - before})")
    conn.close()


if __name__ == "__main__":
    fetch_more_autos()
