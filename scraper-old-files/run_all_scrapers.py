"""
51.ca 主爬蟲 - 爬取所有資料
使用 subprocess 分別運行每個爬蟲，避免 asyncio loop 衝突
"""
import sys
import time
import subprocess
import argparse
from datetime import datetime

from models import init_database, get_connection


def get_stats():
    """獲取當前資料庫統計"""
    conn = get_connection()
    c = conn.cursor()
    stats = {}
    tables = ['news_articles', 'house_listings', 'job_listings', 
              'service_merchants', 'service_posts', 'market_posts', 'auto_listings']
    for table in tables:
        try:
            c.execute(f'SELECT COUNT(*) FROM {table}')
            stats[table] = c.fetchone()[0]
        except:
            stats[table] = 0
    conn.close()
    return stats


def print_stats(stats, title="資料庫統計"):
    """打印統計資訊"""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")
    labels = {
        'news_articles': '📰 新聞',
        'house_listings': '🏠 房源',
        'job_listings': '💼 工作',
        'service_merchants': '🏪 商家',
        'service_posts': '🔧 服務帖',
        'market_posts': '🛒 集市',
        'auto_listings': '🚗 汽車',
    }
    total = 0
    for table, count in stats.items():
        label = labels.get(table, table)
        print(f"  {label}: {count}")
        total += count
    print(f"{'='*50}")
    print(f"  總計: {total}")
    print(f"{'='*50}\n")
    return total


def run_scraper_subprocess(scraper_file: str, name: str, max_pages: int = 5):
    """使用 subprocess 運行單個爬蟲"""
    print(f"\n{'='*60}")
    print(f"  開始爬取: {name}")
    print(f"{'='*60}")
    
    python_exe = sys.executable
    
    try:
        result = subprocess.run(
            [python_exe, scraper_file, '--max-pages', str(max_pages)],
            cwd='.',
            timeout=600  # 10 分鐘超時
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"  ⚠️ 超時")
        return False
    except Exception as e:
        print(f"  ❌ 錯誤: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='51.ca 主爬蟲')
    parser.add_argument('--scrapers', nargs='+', 
                       choices=['news', 'house', 'jobs', 'service', 'market', 'auto', 'merchant', 'all'],
                       default=['all'],
                       help='要運行的爬蟲 (預設: all)')
    parser.add_argument('--max-pages', type=int, default=5,
                       help='每個爬蟲最多爬取的頁數 (預設: 5)')
    args = parser.parse_args()
    
    print(f"\n{'#'*60}")
    print(f"  51.ca 主爬蟲")
    print(f"  時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")
    
    # 初始化資料庫
    init_database()
    
    # 爬取前統計
    before_stats = get_stats()
    print_stats(before_stats, "爬取前統計")
    
    # 確定要運行的爬蟲
    scrapers_to_run = args.scrapers
    if 'all' in scrapers_to_run:
        scrapers_to_run = ['news', 'house', 'jobs', 'service', 'market', 'auto', 'merchant']
    
    start_time = time.time()
    results = {}
    
    # 爬蟲對應的文件和標籤
    scraper_files = {
        'news': ('51_scraper_news.py', '新聞'),
        'house': ('51_scraper_house.py', '房源'),
        'jobs': ('51_scraper_jobs.py', '工作'),
        'service': ('51_scraper_service.py', '服務'),
        'market': ('51_scraper_market.py', '集市'),
        'auto': ('51_scraper_auto.py', '汽車'),
        'merchant': ('51_scraper_merchant.py', '商家'),
    }
    
    # 使用 subprocess 運行爬蟲
    for scraper_name in scrapers_to_run:
        if scraper_name in scraper_files:
            file, label = scraper_files[scraper_name]
            results[scraper_name] = run_scraper_subprocess(file, label, args.max_pages)
    
    # 爬取後統計
    after_stats = get_stats()
    print_stats(after_stats, "爬取後統計")
    
    # 計算新增數量
    print(f"\n{'='*50}")
    print(f"  新增資料統計")
    print(f"{'='*50}")
    total_new = 0
    labels = {
        'news_articles': '📰 新聞',
        'house_listings': '🏠 房源',
        'job_listings': '💼 工作',
        'service_merchants': '🏪 商家',
        'service_posts': '🔧 服務帖',
        'market_posts': '🛒 集市',
        'auto_listings': '🚗 汽車',
    }
    for table in after_stats:
        new_count = after_stats[table] - before_stats.get(table, 0)
        if new_count > 0:
            label = labels.get(table, table)
            print(f"  {label}: +{new_count}")
            total_new += new_count
    print(f"{'='*50}")
    print(f"  總計新增: +{total_new}")
    print(f"{'='*50}")
    
    # 執行時間
    elapsed = time.time() - start_time
    print(f"\n⏱️ 總執行時間: {elapsed:.1f} 秒")
    
    # 結果摘要
    print(f"\n{'='*50}")
    print(f"  執行結果")
    print(f"{'='*50}")
    for name, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"  {name}: {status}")
    print(f"{'='*50}\n")


if __name__ == '__main__':
    main()
