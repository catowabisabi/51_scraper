# -*- coding: utf-8 -*-
"""分析 51.ca/market 頁面結構"""
import asyncio
from playwright.async_api import async_playwright

async def analyze_market():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 訪問集市首頁
        print("正在訪問 https://www.51.ca/market/ ...")
        await page.goto("https://www.51.ca/market/", wait_until="networkidle", timeout=30000)
        
        # 等待內容載入
        await page.wait_for_timeout(3000)
        
        # 獲取頁面 HTML
        html = await page.content()
        
        # 保存 HTML 供分析
        with open("data/market_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("HTML 已保存到 data/market_page.html")
        
        # 嘗試找商品連結
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        
        # 找所有包含 market 的連結
        links = soup.find_all('a', href=True)
        market_links = []
        for link in links:
            href = link.get('href', '')
            # 匹配 /market/category/id 格式
            if '/market/' in href and any(c.isdigit() for c in href.split('/')[-1]):
                if href not in market_links:
                    market_links.append(href)
        
        print(f"\n找到 {len(market_links)} 個商品連結:")
        for link in market_links[:20]:
            print(f"  {link}")
        
        # 查看頁面結構 - 商品卡片
        print("\n\n=== 頁面結構分析 ===")
        
        # 常見的商品卡片 class
        card_selectors = [
            '.item-card', '.product-card', '.goods-card', '.list-item',
            '.card', '[class*="item"]', '[class*="goods"]', '[class*="product"]'
        ]
        
        for selector in card_selectors:
            elements = soup.select(selector)
            if elements:
                print(f"\n{selector}: 找到 {len(elements)} 個")
                if elements:
                    # 顯示第一個的結構
                    el = elements[0]
                    print(f"  結構: {el.name}.{el.get('class', [])}")
                    
        # 也看看詳情頁
        print("\n\n正在訪問商品詳情頁...")
        await page.goto("https://www.51.ca/market/books/103154", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        
        detail_html = await page.content()
        with open("data/market_detail.html", "w", encoding="utf-8") as f:
            f.write(detail_html)
        print("詳情頁 HTML 已保存到 data/market_detail.html")
        
        detail_soup = BeautifulSoup(detail_html, 'lxml')
        
        # 找標題
        title_selectors = ['h1', '.title', '.goods-title', '.detail-title', '[class*="title"]']
        for sel in title_selectors:
            el = detail_soup.select_one(sel)
            if el:
                text = el.get_text(strip=True)[:50]
                print(f"  {sel}: {text}")
        
        # 找價格
        price_selectors = ['.price', '[class*="price"]', '.amount']
        for sel in price_selectors:
            el = detail_soup.select_one(sel)
            if el:
                text = el.get_text(strip=True)[:30]
                print(f"  {sel}: {text}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_market())
