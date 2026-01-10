#!/usr/bin/env python3
"""運行修正後的汽車爬蟲"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scraper'))

# 導入爬蟲模組
from scraper import *

def main():
    """運行汽車爬蟲"""
    print("開始運行修正後的汽車爬蟲...")
    
    try:
        scraper = AutoScraper(headless=True)
        scraper.run_auto_scraper(max_pages=20)
        print("汽車爬蟲運行完成!")
        
        # 檢查更新後的資料
        print("\n檢查更新後的資料...")
        import sqlite3
        conn = sqlite3.connect('data/51ca.db')
        cursor = conn.cursor()
        
        # 檢查NULL值統計
        cursor.execute('SELECT COUNT(*) FROM auto_listings')
        total = cursor.fetchone()[0]
        print(f"總計汽車記錄: {total}")
        
        null_fields = ['listing_type', 'price', 'location', 'post_date', 'vin', 'seller_name']
        for field in null_fields:
            cursor.execute(f'SELECT COUNT(*) FROM auto_listings WHERE {field} IS NOT NULL')
            non_null = cursor.fetchone()[0]
            cursor.execute(f'SELECT COUNT(*) FROM auto_listings WHERE {field} IS NULL')
            null_count = cursor.fetchone()[0]
            print(f"{field}: {non_null} 有值, {null_count} NULL")
            
        conn.close()
        
    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()