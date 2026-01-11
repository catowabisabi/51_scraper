"""
测试从详情页获取解密的电话号码
"""
import asyncio
import json
import re
from playwright.async_api import async_playwright

async def test_phone_decrypt():
    """测试点击 '查看电话' 按钮获取电话号码"""
    
    # 测试几个固定的商品
    test_items = [
        ('103685', '沙發', 'https://www.51.ca/market/furniture/103685'),
        ('103674', '古董鋼琴', 'https://www.51.ca/market/musical-instruments/103674'),
        ('103666', '加拿大鹅', 'https://www.51.ca/market/costume-matching/103666'),
    ]
    
    print(f"测试 {len(test_items)} 个商品的电话解密...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 监听所有网络请求和响应
        async def log_response(response):
            url = response.url
            # 打印所有 API 请求
            if '/web/api/' in url or '/api/' in url:
                print(f"  [API] {response.request.method} {url}")
                try:
                    body = await response.text()
                    if body:
                        print(f"  [BODY] {body[:300]}...")
                except:
                    pass
        
        page.on('response', log_response)
        
        for post_id, title, url in test_items:
            print(f"\n{'='*60}")
            print(f"测试: {post_id} - {title}")
            print(f"URL: {url}")
            
            try:
                # 访问详情页
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(2)
                
                # 获取页面 HTML 中的 __NEXT_DATA__
                next_data = await page.evaluate('''() => {
                    const script = document.getElementById('__NEXT_DATA__');
                    return script ? JSON.parse(script.textContent) : null;
                }''')
                
                if next_data:
                    data = next_data.get('props', {}).get('pageProps', {}).get('data', {})
                    print(f"从 __NEXT_DATA__ 获取:")
                    print(f"  encryptPhone: {data.get('encryptPhone', 'N/A')[:50]}...")
                    print(f"  email: {data.get('email', 'N/A')}")
                    print(f"  wechatNo: {data.get('wechatNo', 'N/A')}")
                
                # 查找 "查看电话" 按钮
                phone_btn = page.locator('button:has-text("查看电话")')
                
                if await phone_btn.count() > 0:
                    print("\n找到 '查看电话' 按钮，点击...")
                    
                    # 获取按钮父元素的 HTML
                    parent_html_before = await phone_btn.evaluate('el => el.parentElement.outerHTML')
                    print(f"点击前 HTML: {parent_html_before[:200]}...")
                    
                    # 点击按钮
                    await phone_btn.click()
                    await asyncio.sleep(2)
                    
                    # 获取点击后的 HTML
                    parent_html_after = await phone_btn.evaluate('el => el.parentElement.outerHTML')
                    print(f"点击后 HTML: {parent_html_after[:200]}...")
                    
                    # 检查是否有变化
                    if parent_html_before != parent_html_after:
                        print("✓ HTML 发生变化!")
                        # 查找电话号码格式
                        phone_match = re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', parent_html_after)
                        if phone_match:
                            print(f"✓ 找到电话: {phone_match.group()}")
                    else:
                        print("✗ HTML 没有变化")
                    
                    # 检查所有 a[href^="tel:"] 链接
                    tel_links = await page.locator('a[href^="tel:"]').all()
                    print(f"页面上的 tel: 链接数量: {len(tel_links)}")
                    for tel in tel_links:
                        href = await tel.get_attribute('href')
                        text = await tel.text_content()
                        print(f"  tel链接: {href} (文本: {text})")
                    
                    # 检查页面上所有包含电话格式的文本
                    page_text = await page.evaluate('() => document.body.innerText')
                    phone_numbers = re.findall(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', page_text)
                    if phone_numbers:
                        print(f"页面上找到的电话号码: {phone_numbers}")
                    
                else:
                    print("未找到 '查看电话' 按钮")
                    
            except Exception as e:
                print(f"错误: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n测试完成。按 Enter 关闭浏览器...")
        await asyncio.sleep(30)  # 等待30秒让用户查看
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_phone_decrypt())
