#!/usr/bin/env python3
"""測試汽車爬蟲的修正版本"""

import sys
import os
import requests
from bs4 import BeautifulSoup

# 添加scraper目錄到path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scraper'))

def test_auto_extraction():
    """測試汽車信息提取"""
    print("測試汽車信息提取...")
    
    # 獲取測試頁面
    test_url = 'https://www.51.ca/autos/used-cars/10021'
    print(f"測試URL: {test_url}")
    
    try:
        response = requests.get(test_url, timeout=10)
        response.raise_for_status()
        html = response.text
        print("✓ 成功獲取頁面")
        
        # 解析頁面
        soup = BeautifulSoup(html, "lxml")
        
        # 測試提取函數
        results = {}
        
        # 提取listing_type
        if '/used-cars/' in test_url:
            results['listing_type'] = '二手'
        elif '/new-cars/' in test_url:
            results['listing_type'] = '新車'
        elif '/lease-cars/' in test_url:
            results['listing_type'] = '轉lease'
        
        # 提取價格
        text = soup.get_text()
        import re
        price_match = re.search(r'\$\s*([\d,]+(?:\.\d{2})?)', text)
        if price_match:
            results['price'] = float(price_match.group(1).replace(',', ''))
        
        # 提取位置
        canadian_cities = [
            'Toronto', 'Mississauga', 'Brampton', 'Hamilton', 'London', 'Markham',
            'Vaughan', 'Kitchener', 'Windsor', 'Richmond Hill', 'Oakville', 
            'Burlington', 'Barrie', 'Oshawa', 'Cambridge', 'Kingston', 'Whitby',
            'Scarborough', 'North York', 'Etobicoke', 'Newmarket'
        ]
        
        for city in canadian_cities:
            if city.lower() in text.lower():
                results['location'] = city
                break
        
        # 提取發布時間
        time_patterns = [
            r'(\d+)\s*小时前',
            r'(\d+)\s*天前',
            r'昨天',
            r'今天'
        ]
        
        from datetime import datetime, timedelta
        for pattern in time_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                if '小时前' in match.group(0):
                    hours = int(match.group(1))
                    post_time = datetime.now() - timedelta(hours=hours)
                    results['post_date'] = post_time.strftime('%Y-%m-%d %H:%M:%S')
                elif '天前' in match.group(0):
                    days = int(match.group(1))
                    post_time = datetime.now() - timedelta(days=days)
                    results['post_date'] = post_time.strftime('%Y-%m-%d %H:%M:%S')
                break
        
        # 顯示結果
        print("\n提取結果:")
        print("=" * 50)
        for key, value in results.items():
            print(f"{key:15}: {value}")
            
        # 檢查關鍵字段
        print("\n關鍵字段檢查:")
        key_fields = ['listing_type', 'price', 'location', 'post_date']
        for field in key_fields:
            value = results.get(field)
            status = "✓ 有值" if value else "✗ NULL"
            print(f"{field:15}: {status}")
            
    except Exception as e:
        print(f"✗ 錯誤: {e}")

if __name__ == "__main__":
    test_auto_extraction()