"""简化测试 - 直接获取10个商品的解密电话"""
import json
import re
import time
import sqlite3
from playwright.sync_api import sync_playwright

def test_phone_decrypt():
    print("测试获取解密电话...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # 先访问列表页获取一些商品ID
        page.goto('https://www.51.ca/market/all', wait_until='networkidle', timeout=30000)
        time.sleep(2)
        
        # 从 __NEXT_DATA__ 获取商品列表
        next_data = page.evaluate('''() => {
            const el = document.getElementById('__NEXT_DATA__');
            return el ? JSON.parse(el.textContent) : null;
        }''')
        
        if not next_data:
            print("无法获取数据")
            browser.close()
            return
        
        init_data = next_data.get('props', {}).get('pageProps', {}).get('initData', {})
        items = init_data.get('data', [])
        
        # 过滤 market 来源
        market_items = [i for i in items if i.get('source') == 'market'][:10]
        print(f"找到 {len(market_items)} 个商品")
        
        results = []
        
        for item in market_items:
            item_id = item.get('id')
            cat_slug = item.get('categorySlug', 'all')
            title = item.get('title', '')[:30]
            
            print(f"\n处理: {item_id} - {title}...")
            
            try:
                # 访问详情页
                detail_url = f"https://www.51.ca/market/{cat_slug}/{item_id}"
                page.goto(detail_url, wait_until='networkidle', timeout=15000)
                time.sleep(1)
                
                # 点击查看电话
                phone_btn = page.locator('button:has-text("查看电话")')
                if phone_btn.count() > 0:
                    phone_btn.click()
                    time.sleep(0.8)
                    
                    # 点击知道了
                    confirm_btn = page.locator('button:has-text("知道了")')
                    if confirm_btn.count() > 0:
                        confirm_btn.click()
                        time.sleep(0.8)
                    
                    # 获取电话 - 尝试多种方式
                    phone = None
                    
                    # 方法1: 从 tel: 链接获取
                    tel_link = page.locator('a[href^="tel:"]')
                    if tel_link.count() > 0:
                        href = tel_link.get_attribute('href')
                        if href:
                            phone = href.replace('tel:', '').strip()
                    
                    # 方法2: 从按钮文本获取
                    if not phone:
                        tel_btn = page.locator('button.telPopover')
                        if tel_btn.count() > 0:
                            btn_text = tel_btn.inner_text()
                            phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', btn_text)
                            if phone_match:
                                phone = phone_match.group().strip()
                    
                    # 方法3: 从页面任何位置获取
                    if not phone:
                        page_text = page.inner_text('body')
                        phone_matches = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', page_text)
                        if phone_matches:
                            phone = phone_matches[0]
                    
                    if phone:
                        print(f"  ✓ 电话: {phone}")
                        results.append({
                            'id': item_id,
                            'title': title,
                            'category': cat_slug,
                            'phone': phone,
                            'email': item.get('email', '')
                        })
                    else:
                        print(f"  ✗ 无电话号码")
                else:
                    print(f"  - 没有查看电话按钮")
            except Exception as e:
                print(f"  错误: {e}")
        
        browser.close()
        
        print(f"\n{'='*60}")
        print(f"成功获取 {len(results)}/10 个电话")
        print(f"{'='*60}")
        for r in results:
            print(f"  {r['id']}: {r['title']} | {r['phone']}")
        
        # 保存到数据库
        if results:
            print(f"\n更新数据库中的电话...")
            conn = sqlite3.connect('scrapers/data/51ca.db')
            c = conn.cursor()
            for r in results:
                c.execute('''
                    UPDATE market_posts 
                    SET contact_phone = ? 
                    WHERE post_id = ?
                ''', (r['phone'], str(r['id'])))
            conn.commit()
            conn.close()
            print(f"已更新 {len(results)} 条记录")

if __name__ == '__main__':
    test_phone_decrypt()
