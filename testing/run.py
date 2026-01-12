#!/usr/bin/env python3
"""
51.ca 爬蟲統一運行入口
提供 CLI 介面來運行各類爬蟲

使用方法:
    python run.py --all              # 運行所有爬蟲
    python run.py --news             # 只運行新聞爬蟲
    python run.py --house --auto     # 運行房屋和汽車爬蟲
    python run.py --list             # 列出所有可用爬蟲
    python run.py --stats            # 顯示資料庫統計
    python run.py --init             # 初始化資料庫
"""

import argparse
import sys
import os
from datetime import datetime

# 添加 scrapers 目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.models import init_database, get_connection


# 爬蟲映射
SCRAPERS = {
    'news': ('scrapers.news_scraper', 'NewsScraper', '新聞爬蟲 (info.51.ca)'),
    'house': ('scrapers.house_scraper', 'HouseScraper', '房屋爬蟲 (house.51.ca)'),
    'market': ('scrapers.market_scraper', 'MarketScraper', '集市爬蟲 (市場二手物品)'),
    'auto': ('scrapers.auto_scraper', 'AutoScraper', '汽車爬蟲 (二手車/新車/轉lease)'),
    'event': ('scrapers.event_scraper', 'EventScraper', '活動爬蟲 (社區活動)'),
}


def get_scraper(name: str):
    """動態載入爬蟲類"""
    if name not in SCRAPERS:
        raise ValueError(f"未知爬蟲: {name}")
    
    module_name, class_name, _ = SCRAPERS[name]
    
    import importlib
    module = importlib.import_module(module_name)
    scraper_class = getattr(module, class_name)
    
    return scraper_class()


def run_scraper(name: str, max_pages: int = 50, use_browser: bool = False):
    """運行單個爬蟲"""
    print(f"\n{'='*60}")
    print(f"開始運行: {SCRAPERS[name][2]}")
    print(f"{'='*60}")
    
    try:
        scraper = get_scraper(name)
        if use_browser:
            scraper.use_browser = True
        scraper.run(max_pages=max_pages)
        return True
    except Exception as e:
        print(f"爬蟲 {name} 運行錯誤: {e}")
        return False


def run_all_scrapers(max_pages: int = 30):
    """運行所有爬蟲"""
    print("\n" + "="*60)
    print("開始運行所有爬蟲")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {}
    for name in SCRAPERS:
        success = run_scraper(name, max_pages=max_pages)
        results[name] = '✓ 成功' if success else '✗ 失敗'
    
    print("\n" + "="*60)
    print("運行結果:")
    for name, result in results.items():
        print(f"  {SCRAPERS[name][2]}: {result}")
    print("="*60)


def show_stats():
    """顯示資料庫統計"""
    conn = get_connection()
    cursor = conn.cursor()
    
    tables = [
        ('news_articles', '新聞文章'),
        ('house_listings', '房屋列表'),
        ('market_posts', '集市商品'),
        ('auto_listings', '汽車列表'),
        ('events', '社區活動'),
        ('url_queue', 'URL隊列'),
    ]
    
    print("\n" + "="*60)
    print("資料庫統計 (51ca.db)")
    print("="*60)
    
    for table_name, display_name in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {display_name}: {count} 筆")
        except:
            print(f"  {display_name}: (表不存在)")
    
    conn.close()
    print("="*60)


def list_scrapers():
    """列出所有可用爬蟲"""
    print("\n" + "="*60)
    print("可用爬蟲列表:")
    print("="*60)
    
    for name, (_, _, desc) in SCRAPERS.items():
        print(f"  --{name:10} : {desc}")
    
    print("\n使用示例:")
    print("  python run.py --all          # 運行所有爬蟲")
    print("  python run.py --news         # 只運行新聞爬蟲")
    print("  python run.py --house --auto # 運行多個爬蟲")
    print("  python run.py --max 100      # 設置最大頁數")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description='51.ca 爬蟲系統',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py --all              運行所有爬蟲
  python run.py --news --house     運行新聞和房屋爬蟲
  python run.py --auto --max 100   運行汽車爬蟲，最多100頁
  python run.py --stats            顯示資料庫統計
        """
    )
    
    # 爬蟲選項
    parser.add_argument('--all', action='store_true', help='運行所有爬蟲')
    parser.add_argument('--news', action='store_true', help='運行新聞爬蟲')
    parser.add_argument('--house', action='store_true', help='運行房屋爬蟲')
    parser.add_argument('--market', action='store_true', help='運行集市爬蟲')
    parser.add_argument('--auto', action='store_true', help='運行汽車爬蟲')
    parser.add_argument('--event', action='store_true', help='運行活動爬蟲')
    
    # 配置選項
    parser.add_argument('--max', type=int, default=50, help='最大頁數 (默認: 50)')
    parser.add_argument('--browser', action='store_true', help='使用瀏覽器模式')
    
    # 工具選項
    parser.add_argument('--list', action='store_true', help='列出所有可用爬蟲')
    parser.add_argument('--stats', action='store_true', help='顯示資料庫統計')
    parser.add_argument('--init', action='store_true', help='初始化資料庫')
    
    args = parser.parse_args()
    
    # 處理工具命令
    if args.list:
        list_scrapers()
        return
    
    if args.stats:
        show_stats()
        return
    
    if args.init:
        print("正在初始化資料庫...")
        init_database()
        print("資料庫初始化完成!")
        show_stats()
        return
    
    # 處理爬蟲命令
    if args.all:
        run_all_scrapers(max_pages=args.max)
        return
    
    # 運行指定爬蟲
    scrapers_to_run = []
    if args.news:
        scrapers_to_run.append('news')
    if args.house:
        scrapers_to_run.append('house')
    if args.market:
        scrapers_to_run.append('market')
    if args.auto:
        scrapers_to_run.append('auto')
    if args.event:
        scrapers_to_run.append('event')
    
    if scrapers_to_run:
        for name in scrapers_to_run:
            run_scraper(name, max_pages=args.max, use_browser=args.browser)
        show_stats()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
