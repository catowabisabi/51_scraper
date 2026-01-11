"""
運行所有爬蟲
每個爬蟲爬取約 1000 個項目
"""

import sys
import os
import time
from datetime import datetime

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_all_scrapers():
    """運行所有爬蟲"""
    
    print("=" * 60)
    print(f"開始運行所有爬蟲 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {}
    
    # 1. 新聞爬蟲 (約 200 頁)
    print("\n" + "=" * 60)
    print("1. 運行新聞爬蟲...")
    print("=" * 60)
    try:
        from scrapers.news_scraper import NewsScraper
        scraper = NewsScraper(use_browser=True, headless=True)
        scraper.run(max_pages=200)
        results['news'] = scraper.stats
    except Exception as e:
        print(f"新聞爬蟲錯誤: {e}")
        import traceback
        traceback.print_exc()
        results['news'] = {'error': str(e)}
    
    time.sleep(5)
    
    # 2. 工作爬蟲 (使用專門的 run 方法)
    print("\n" + "=" * 60)
    print("2. 運行工作爬蟲...")
    print("=" * 60)
    try:
        from scrapers.jobs_scraper import JobsScraper
        scraper = JobsScraper()
        jobs = scraper.run(max_jobs=1000, fetch_details=True, headless=True)
        results['jobs'] = {'items_saved': len(jobs) if jobs else 0}
    except Exception as e:
        print(f"工作爬蟲錯誤: {e}")
        import traceback
        traceback.print_exc()
        results['jobs'] = {'error': str(e)}
    
    time.sleep(5)
    
    # 3. 房屋爬蟲
    print("\n" + "=" * 60)
    print("3. 運行房屋爬蟲...")
    print("=" * 60)
    try:
        from scrapers.house_scraper import HouseScraper
        scraper = HouseScraper()
        scraper.run(max_pages=200)
        results['house'] = scraper.stats
    except Exception as e:
        print(f"房屋爬蟲錯誤: {e}")
        import traceback
        traceback.print_exc()
        results['house'] = {'error': str(e)}
    
    time.sleep(5)
    
    # 4. 集市爬蟲
    print("\n" + "=" * 60)
    print("4. 運行集市爬蟲...")
    print("=" * 60)
    try:
        from scrapers.market_scraper import MarketScraper
        scraper = MarketScraper()
        scraper.run(max_pages=200)
        results['market'] = scraper.stats
    except Exception as e:
        print(f"集市爬蟲錯誤: {e}")
        import traceback
        traceback.print_exc()
        results['market'] = {'error': str(e)}
    
    time.sleep(5)
    
    # 5. 汽車爬蟲
    print("\n" + "=" * 60)
    print("5. 運行汽車爬蟲...")
    print("=" * 60)
    try:
        from scrapers.auto_scraper import AutoScraper
        scraper = AutoScraper()
        scraper.run(max_pages=200)
        results['auto'] = scraper.stats
    except Exception as e:
        print(f"汽車爬蟲錯誤: {e}")
        import traceback
        traceback.print_exc()
        results['auto'] = {'error': str(e)}
    
    time.sleep(5)
    
    # 6. 活動爬蟲
    print("\n" + "=" * 60)
    print("6. 運行活動爬蟲...")
    print("=" * 60)
    try:
        from scrapers.event_scraper import EventScraper
        scraper = EventScraper()
        scraper.run(max_pages=200)
        results['event'] = scraper.stats
    except Exception as e:
        print(f"活動爬蟲錯誤: {e}")
        import traceback
        traceback.print_exc()
        results['event'] = {'error': str(e)}
    
    # 打印總結
    print("\n" + "=" * 60)
    print("所有爬蟲運行完成!")
    print("=" * 60)
    
    for name, stats in results.items():
        if 'error' in stats:
            print(f"  {name}: 錯誤 - {stats['error']}")
        else:
            pages = stats.get('pages_scraped', 'N/A')
            items = stats.get('items_saved', 'N/A')
            errors = stats.get('errors', 'N/A')
            print(f"  {name}: 頁面={pages}, 項目={items}, 錯誤={errors}")
    
    return results


if __name__ == "__main__":
    run_all_scrapers()
