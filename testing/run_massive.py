"""
大量爬取腳本 - 獲取更多數據
"""

import subprocess
import sys
import os
from datetime import datetime

def run_scraper_in_background(name, command):
    """在背景運行爬蟲"""
    print(f"🚀 啟動 {name} 爬蟲...")
    try:
        process = subprocess.Popen(
            command,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"✅ {name} 爬蟲已啟動 (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ {name} 爬蟲啟動失敗: {e}")
        return None

def main():
    """大量爬取更多數據"""
    print("=" * 60)
    print("🔥 開始大量爬取數據!")
    print("=" * 60)
    
    processes = []
    
    # 1. 工作爬蟲 - 目標3000個工作
    if True:
        cmd = [sys.executable, "-m", "scrapers.jobs_scraper", "--max-jobs", "3000"]
        p = run_scraper_in_background("工作", cmd)
        if p: processes.append(("工作", p))
    
    # 2. 新聞爬蟲 - 更多頁面
    if True:
        cmd = [sys.executable, "-m", "scrapers.news_scraper"]
        p = run_scraper_in_background("新聞", cmd)  
        if p: processes.append(("新聞", p))
    
    # 3. 房屋爬蟲 - 使用瀏覽器版本獲取詳情
    if True:
        cmd = [sys.executable, "-c", """
from scrapers.house_scraper import HouseScraper
scraper = HouseScraper()
scraper.run_full_scrape(max_pages_per_type=20, fetch_details=True)
"""]
        p = run_scraper_in_background("房屋詳情", cmd)
        if p: processes.append(("房屋詳情", p))
    
    # 4. 集市爬蟲 - 多個分類
    if True:
        cmd = [sys.executable, "-c", """
from scrapers.market_scraper import MarketScraper
scraper = MarketScraper()
scraper.run_all_categories(max_pages_per_category=10)
"""]
        p = run_scraper_in_background("集市分類", cmd)
        if p: processes.append(("集市分類", p))
    
    print(f"\n🎯 已啟動 {len(processes)} 個爬蟲")
    print("⏳ 爬蟲正在背景運行，請使用 python check_all_data.py 查看進度")
    
    return processes

if __name__ == "__main__":
    main()