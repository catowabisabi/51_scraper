"""测试 market 网站的无限滚动"""
from playwright.sync_api import sync_playwright
import time

def test_scroll():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # 监听所有网络请求
        def on_request(request):
            if '51.ca' in request.url and ('api' in request.url or 'json' in request.url):
                print(f"[REQ] {request.method} {request.url}")
        
        def on_response(response):
            if '51.ca' in response.url and ('api' in response.url or 'json' in response.url):
                print(f"[RES] {response.status} {response.url[:100]}")
        
        page.on("request", on_request)
        page.on("response", on_response)
        
        print("访问页面...")
        page.goto("https://www.51.ca/market/all")
        page.wait_for_load_state('networkidle')
        
        print("\n等待3秒...")
        time.sleep(3)
        
        # 检查页面上的元素
        print("\n检查页面结构...")
        
        # 查找"加载更多"按钮
        load_more = page.query_selector('button:has-text("加载更多"), button:has-text("Load More"), .load-more')
        if load_more:
            print(f"找到加载更多按钮: {load_more.text_content()}")
        else:
            print("没有找到加载更多按钮")
        
        # 查找分页按钮
        pagination = page.query_selector('.pagination, [class*="pagination"], [class*="Pagination"]')
        if pagination:
            print(f"找到分页元素")
        else:
            print("没有找到分页元素")
        
        # 滚动测试
        print("\n开始滚动测试...")
        for i in range(5):
            print(f"\n--- 滚动 #{i+1} ---")
            
            # 获取当前商品数量
            items = page.query_selector_all('[class*="ProductCard"], [class*="product"], [class*="item"]')
            print(f"当前页面商品数量: {len(items)}")
            
            # 滚动到底部
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            print("滚动到底部")
            
            time.sleep(2)
            
            # 再次获取商品数量
            items = page.query_selector_all('[class*="ProductCard"], [class*="product"], [class*="item"]')
            print(f"滚动后商品数量: {len(items)}")
        
        print("\n保持浏览器打开10秒以便查看...")
        time.sleep(10)
        
        browser.close()

if __name__ == "__main__":
    test_scroll()
