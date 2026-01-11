"""测试详情页获取电话号码 - 带确认弹窗"""
import asyncio
from playwright.async_api import async_playwright
import re

async def test_phone():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 显示浏览器方便调试
        context = await browser.new_context()
        page = await context.new_page()
        
        # 测试几个商品ID
        test_ids = [
            ('furniture', 103685),
            ('costume-matching', 103666),
            ('electronics', 103654),
            ('home-appliance', 103674),
            ('kitchen-supplies', 103606),
            ('exerciser', 103556),
            ('books', 103541),
            ('gardening', 103520),
            ('health', 103510),
            ('others', 103500),
        ]
        
        results = []
        
        for category, item_id in test_ids[:10]:
            url = f"https://www.51.ca/market/{category}/{item_id}"
            print(f"\n=== Testing {url} ===")
            
            try:
                await page.goto(url, wait_until='networkidle', timeout=15000)
                await asyncio.sleep(1)
                
                # 找到"查看电话"按钮并点击
                phone_btn = page.locator('button:has-text("查看电话")')
                if await phone_btn.count() > 0:
                    print("Found '查看电话' button, clicking...")
                    await phone_btn.click()
                    await asyncio.sleep(1)
                    
                    # 等待并点击"知道了"确认弹窗
                    confirm_btn = page.locator('button:has-text("知道了")')
                    if await confirm_btn.count() > 0:
                        print("Found '知道了' button, clicking...")
                        await confirm_btn.click()
                        await asyncio.sleep(1)
                    
                    # 检查按钮内容是否变化（应该显示电话号码）
                    # 可能按钮已经不存在了，需要重新查找
                    try:
                        # 尝试找包含电话的元素
                        tel_link = page.locator('a[href^="tel:"]')
                        if await tel_link.count() > 0:
                            href = await tel_link.get_attribute('href')
                            phone = href.replace('tel:', '').strip()
                            print(f"✓ Found tel link: {phone}")
                            results.append({
                                'id': item_id,
                                'category': category,
                                'phone': phone
                            })
                        else:
                            # 尝试从按钮文本获取
                            phone_btn = page.locator('button.telPopover')
                            if await phone_btn.count() > 0:
                                btn_text = await phone_btn.inner_text()
                                print(f"Button text: '{btn_text}'")
                                phone_match = re.search(r'[\d\-\(\)\s]{7,}', btn_text)
                                if phone_match:
                                    phone = phone_match.group().strip()
                                    print(f"✓ Extracted phone: {phone}")
                                    results.append({
                                        'id': item_id,
                                        'category': category,
                                        'phone': phone
                                    })
                            
                            # 也搜索整个页面
                            page_text = await page.inner_text('body')
                            # 匹配北美电话格式
                            phone_patterns = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', page_text)
                            if phone_patterns and item_id not in [r['id'] for r in results]:
                                print(f"✓ Found phone in page: {phone_patterns[0]}")
                                results.append({
                                    'id': item_id,
                                    'category': category,
                                    'phone': phone_patterns[0]
                                })
                            elif item_id not in [r['id'] for r in results]:
                                print(f"✗ No phone number found")
                    except Exception as e:
                        print(f"Error getting phone: {e}")
                else:
                    print("No '查看电话' button found")
            except Exception as e:
                print(f"Error: {e}")
        
        await browser.close()
        
        print(f"\n{'='*50}")
        print(f"=== Results: {len(results)}/{len(test_ids[:10])} phones found ===")
        print(f"{'='*50}")
        for r in results:
            print(f"  {r['category']}/{r['id']}: {r['phone']}")

asyncio.run(test_phone())
