"""
導入所有爬蟲模塊
"""

# 使用延遲導入避免循環依賴
def get_news_scraper():
    from import_scrapers import NewsScraper
    return NewsScraper

def get_house_scraper():
    from import_scrapers import HouseScraper
    return HouseScraper

def get_jobs_scraper():
    from import_scrapers import JobsScraper
    return JobsScraper


# 直接導入
try:
    from scraper.base_scraper import BaseScraper, setup_logger
except ImportError:
    from base_scraper import BaseScraper, setup_logger

try:
    from scraper.models import *
except ImportError:
    from models import *


# 爬蟲類
class NewsScraper:
    """新聞爬蟲代理類"""
    def __new__(cls, *args, **kwargs):
        try:
            from scraper import NewsScraper as NS
            return NS(*args, **kwargs)
        except ImportError:
            # 直接導入模塊中的類
            import sys
            import os
            sys.path.insert(0, os.path.dirname(__file__))
            from importlib import import_module
            news_module = import_module('51_scraper_news')
            return news_module.NewsScraper(*args, **kwargs)


class HouseScraper:
    """房屋爬蟲代理類"""
    def __new__(cls, *args, **kwargs):
        try:
            from scraper import HouseScraper as HS
            return HS(*args, **kwargs)
        except ImportError:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(__file__))
            from importlib import import_module
            house_module = import_module('51_scraper_house')
            return house_module.HouseScraper(*args, **kwargs)


class JobsScraper:
    """工作爬蟲代理類"""
    def __new__(cls, *args, **kwargs):
        try:
            from scraper import JobsScraper as JS
            return JS(*args, **kwargs)
        except ImportError:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(__file__))
            from importlib import import_module
            jobs_module = import_module('51_scraper_jobs')
            return jobs_module.JobsScraper(*args, **kwargs)


__all__ = ['NewsScraper', 'HouseScraper', 'JobsScraper', 'BaseScraper', 'setup_logger']
