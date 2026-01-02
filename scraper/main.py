"""
51.ca 主爬蟲程式
統一運行所有爬蟲
"""

import sys
import argparse
from datetime import datetime

import os
import sys

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(__file__))

from models import init_database, get_stats
from base_scraper import setup_logger

# 動態導入爬蟲類
def get_scrapers():
    """動態獲取爬蟲類"""
    from importlib import import_module
    
    news_module = import_module('51_scraper_news')
    house_module = import_module('51_scraper_house')
    jobs_module = import_module('51_scraper_jobs')
    service_module = import_module('51_scraper_service')
    market_module = import_module('51_scraper_market')
    auto_module = import_module('51_scraper_auto')
    
    return {
        'news': (news_module.NewsScraper, "run_news_scraper"),
        'house': (house_module.HouseScraper, "run_house_scraper"),
        'jobs': (jobs_module.JobsScraper, "run_jobs_scraper"),
        'service': (service_module.ServiceScraper, "run_service_scraper"),
        'market': (market_module.MarketScraper, "run_market_scraper"),
        'auto': (auto_module.AutoScraper, "run_auto_scraper"),
    }


def run_all_scrapers(max_pages: int = 30, headless: bool = True):
    """運行所有爬蟲"""
    logger = setup_logger("main")
    
    logger.info("=" * 70)
    logger.info("51.ca 全站爬蟲開始運行")
    logger.info(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    # 初始化資料庫
    init_database()
    
    scrapers_dict = get_scrapers()
    scrapers = [
        ("新聞爬蟲", scrapers_dict['news'][0], scrapers_dict['news'][1]),
        ("房屋爬蟲", scrapers_dict['house'][0], scrapers_dict['house'][1]),
        ("工作爬蟲", scrapers_dict['jobs'][0], scrapers_dict['jobs'][1]),
        ("黃頁服務爬蟲", scrapers_dict['service'][0], scrapers_dict['service'][1]),
        ("集市爬蟲", scrapers_dict['market'][0], scrapers_dict['market'][1]),
        ("汽車爬蟲", scrapers_dict['auto'][0], scrapers_dict['auto'][1]),
    ]
    
    for name, ScraperClass, run_method in scrapers:
        logger.info(f"\n{'=' * 50}")
        logger.info(f"開始運行: {name}")
        logger.info(f"{'=' * 50}")
        
        try:
            scraper = ScraperClass(headless=headless)
            getattr(scraper, run_method)(max_pages=max_pages)
        except Exception as e:
            logger.error(f"{name} 運行失敗: {e}")
    
    # 打印統計
    print_final_stats(logger)


def run_single_scraper(scraper_name: str, max_pages: int = 30, headless: bool = True):
    """運行單個爬蟲"""
    logger = setup_logger("main")
    
    scrapers = get_scrapers()
    
    if scraper_name not in scrapers:
        logger.error(f"未知的爬蟲: {scraper_name}")
        logger.info(f"可用的爬蟲: {', '.join(scrapers.keys())}")
        return
    
    ScraperClass, run_method = scrapers[scraper_name]
    
    logger.info(f"運行 {scraper_name} 爬蟲")
    
    try:
        scraper = ScraperClass(headless=headless)
        getattr(scraper, run_method)(max_pages=max_pages)
    except Exception as e:
        logger.error(f"爬蟲運行失敗: {e}")
    
    print_final_stats(logger)


def print_final_stats(logger):
    """打印最終統計"""
    stats = get_stats()
    
    logger.info("\n" + "=" * 70)
    logger.info("📊 資料庫統計:")
    logger.info("-" * 40)
    logger.info(f"  📰 新聞文章: {stats.get('news_articles', 0)} 篇")
    logger.info(f"  🏠 房屋列表: {stats.get('house_listings', 0)} 條")
    logger.info(f"  💼 工作職位: {stats.get('job_listings', 0)} 個")
    logger.info(f"  🏪 黃頁商家: {stats.get('service_merchants', 0)} 家")
    logger.info(f"  📦 集市帖子: {stats.get('market_posts', 0)} 條")
    logger.info(f"  🚗 汽車列表: {stats.get('auto_listings', 0)} 條")
    logger.info("-" * 40)
    logger.info(f"  ⏳ 待爬取URL: {stats.get('pending_urls', 0)}")
    logger.info(f"  ✅ 已爬取URL: {stats.get('visited_urls', 0)}")
    logger.info("=" * 70)


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='51.ca 網站爬蟲')
    parser.add_argument('--scraper', '-s', type=str, default='all',
                        choices=['all', 'news', 'house', 'jobs', 'service', 'market', 'auto'],
                        help='要運行的爬蟲 (默認: all)')
    parser.add_argument('--pages', '-p', type=int, default=30,
                        help='最大爬取頁數 (默認: 30)')
    parser.add_argument('--show', action='store_true',
                        help='顯示瀏覽器視窗')
    
    args = parser.parse_args()
    
    headless = not args.show
    
    if args.scraper == 'all':
        run_all_scrapers(max_pages=args.pages, headless=headless)
    else:
        run_single_scraper(args.scraper, max_pages=args.pages, headless=headless)


if __name__ == "__main__":
    main()
