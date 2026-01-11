"""
简单测试：从10个商品获取解密电话并更新数据库
"""
import sqlite3
import asyncio
from playwright.async_api import async_playwright
import re

async def update_phones():
    """获取解密电话并更新数据库"""
    
    # 获取10个有加密电话但没有解密电话的记录
    conn = sqlite3.connect('scrapers/data/51ca.db')
    c = conn.cursor()
    
    # 获取有加密电话的记录
    c.execute("""
        SELECT post_id, url, contact_phone 
        FROM market_posts 
        WHERE contact_phone IS NOT NULL 
        AND contact_phone != '' 
        AND contact_phone LIKE 'eyJ%'
        LIMIT 10
    """)
    items = c.fetchall()
    print(f"找到 {len(items)} 个需要解密电话的商品")
    
    if not items:
        print("没有需要处理的商品")
        return
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        success_count = 0
        
        for post_id, url, encrypted_phone in items:
            print(f"\n{'='*50}")
            print(f"处理: {post_id} - {url}")
            
            try:
                await page.goto(url, wait_until='networkidle', timeout=15000)
                await asyncio.sleep(1)
                
                # 点击"查看电话"按钮
                phone_btn = page.locator('button:has-text("查看电话")')
                if await phone_btn.count() > 0:
                    await phone_btn.click()
                    await asyncio.sleep(0.5)
                    
                    # 点击"知道了"确认
                    confirm_btn = page.locator('button:has-text("知道了")')
                    if await confirm_btn.count() > 0:
                        await confirm_btn.click()
                        await asyncio.sleep(0.5)
                    
                    # 从按钮文本提取电话
                    phone_btn = page.locator('button.telPopover')
                    if await phone_btn.count() > 0:
                        btn_text = await phone_btn.inner_text()
                        phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', btn_text)
                        if phone_match:
                            phone = phone_match.group().strip()
                            print(f"  ✓ 获取电话: {phone}")
                            
                            # 更新数据库
                            c.execute("""
                                UPDATE market_posts 
                                SET contact_phone = ? 
                                WHERE post_id = ?
                            """, (phone, post_id))
                            conn.commit()
                            success_count += 1
                        else:
                            print(f"  ✗ 无法从按钮文本提取电话: {btn_text[:50]}")
                    else:
                        print(f"  ✗ 找不到 telPopover 按钮")
                else:
                    print(f"  ✗ 找不到'查看电话'按钮")
                    
            except Exception as e:
                print(f"  错误: {e}")
        
        await browser.close()
    
    conn.close()
    print(f"\n{'='*50}")
    print(f"完成: 成功更新 {success_count}/{len(items)} 个电话")

if __name__ == "__main__":
    asyncio.run(update_phones())
