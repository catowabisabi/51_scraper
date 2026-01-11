"""
51.ca 爬蟲模組
導出所有爬蟲類
"""

# 基礎爬蟲
from base_scraper import BaseScraper

# 各類爬蟲
try:
    from importlib import import_module
    
    # 新聞爬蟲
    _news = import_module('51_scraper_news')
    NewsScraper = _news.NewsScraper
except Exception as e:
    print(f"無法導入 NewsScraper: {e}")
    NewsScraper = None

try:
    # 房源爬蟲
    _house = import_module('51_scraper_house')
    HouseScraper = _house.HouseScraper
except Exception as e:
    print(f"無法導入 HouseScraper: {e}")
    HouseScraper = None

try:
    # 工作爬蟲
    _jobs = import_module('51_scraper_jobs')
    JobsScraper = _jobs.JobsScraper
except Exception as e:
    print(f"無法導入 JobsScraper: {e}")
    JobsScraper = None

try:
    # 服務爬蟲
    _service = import_module('51_scraper_service')
    ServiceScraper = _service.ServiceScraper
except Exception as e:
    print(f"無法導入 ServiceScraper: {e}")
    ServiceScraper = None

try:
    # 集市爬蟲
    _market = import_module('51_scraper_market')
    MarketScraper = _market.MarketScraper
except Exception as e:
    print(f"無法導入 MarketScraper: {e}")
    MarketScraper = None

try:
    # 汽車爬蟲
    _auto = import_module('51_scraper_auto')
    AutoScraper = _auto.AutoScraper
except Exception as e:
    print(f"無法導入 AutoScraper: {e}")
    AutoScraper = None

try:
    # 商家爬蟲
    _merchant = import_module('51_scraper_merchant')
    MerchantScraper = _merchant.MerchantScraper
except Exception as e:
    print(f"無法導入 MerchantScraper: {e}")
    MerchantScraper = None

__all__ = [
    'BaseScraper',
    'NewsScraper',
    'HouseScraper', 
    'JobsScraper',
    'ServiceScraper',
    'MarketScraper',
    'AutoScraper',
    'MerchantScraper',
]
