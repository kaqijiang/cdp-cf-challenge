import time
from playwright.sync_api import sync_playwright

# Cloudflare 挑战的标题和选择器
CHALLENGE_TITLES = [
    'Just a moment...',
    'DDoS-Guard'
]

def execute_cdp_command(client, method, params=None):
    """执行 CDP 命令"""
    if params is None:
        params = {}
    try:
        return client.send(method, params)
    except Exception as e:
        print(f"Error executing CDP command {method}: {e}")
        return None

def get_shadow_root_node_id(node):
    """ 递归查找 shadow root 的 nodeId。 """
    if 'shadowRoots' in node and node['shadowRoots']:
        return node['shadowRoots'][0]['nodeId']

    for child in node.get('children', []):
        result = get_shadow_root_node_id(child)
        if result:
            return result
    return None

def click_shadow_dom_checkbox(client, shadow_root_id, checkbox_selector):
    """ 在 shadow DOM 内点击复选框。 """
    checkbox_node = execute_cdp_command(client, "DOM.querySelector", {"nodeId": shadow_root_id, "selector": checkbox_selector})
    if not checkbox_node:
        return False

    checkbox_node_id = checkbox_node.get('nodeId')
    if checkbox_node_id:
        object_info = execute_cdp_command(client, "DOM.resolveNode", {"nodeId": checkbox_node_id})
        if not object_info:
            return False

        object_id = object_info.get('object', {}).get('objectId')
        if object_id:
            execute_cdp_command(client, "Runtime.callFunctionOn", {
                "objectId": object_id,
                "functionDeclaration": "function() { this.click(); }",
                "arguments": [],
                "returnByValue": True
            })
            print(f"Clicked checkbox with Verify you are human")
            return True
    return False

def is_challenge_page(page):
    """检查页面是否为 Cloudflare 挑战页面"""
    try:
        page.wait_for_load_state('networkidle')  # 等待页面网络空闲
        page.wait_for_timeout(200)  # 短暂等待
        page_title = page.title().lower()
        print(page_title)
        return any(title.lower() in page_title for title in CHALLENGE_TITLES)
    except Exception as e:
        print(f"Error checking challenge page: {e}")
        page.wait_for_timeout(200)  # 短暂等待
        return True

def cdp_handle_cloudflare_challenge(page):
    """ 处理 Cloudflare 挑战。"""
    page.wait_for_load_state('networkidle')
    if is_challenge_page(page):
        iframe_url = 'https://challenges.cloudflare.com/cdn-cgi/'
        iframe = next((frame for frame in page.frames if iframe_url in frame.url), None)

        if iframe:
            client = page.context.new_cdp_session(iframe)
            document_info = execute_cdp_command(client, "DOM.getDocument")
            if not document_info:
                return

            root_node = document_info['root']
            shadow_root_id = get_shadow_root_node_id(root_node)
            if not shadow_root_id:
                print("未找到 shadow root 节点")
                return

            max_attempts = 10
            for attempt in range(max_attempts):
                if click_shadow_dom_checkbox(client, shadow_root_id, "input[type='checkbox']"):
                    # 等待页面跳转或内容更新
                    time.sleep(2)
                    # 检查页面是否已通过挑战
                    if not is_challenge_page(page):
                        print("Successfully passed the Cloudflare challenge")
                        return
                    else:
                        print(f"尝试 {attempt + 1}/{max_attempts} 点击复选框成功，但页面仍显示挑战")
                else:
                    print(f"尝试 {attempt + 1}/{max_attempts} 点击复选框失败")
                time.sleep(2)

def main():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=['--accept-lang=en-US'])
            browser = p.chromium.launch(headless=False, args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--window-size=1920,1080',
                '--disable-blink-features=AutomationControlled',
                '--accept-lang=en-US'
            ])
            browser_context = browser.new_context()
            # 在所有新页面创建前执行的脚本
            # 读取 stealth.min.js 文件
            with open('stealth.min.js', 'r') as file:
                stealth_js = file.read()
            browser_context.add_init_script(stealth_js)

            page = browser_context.new_page()

            page.goto("https://faucet.evmos.dev/")
            cdp_handle_cloudflare_challenge(page)
            page.wait_for_timeout(2000)
            # browser.close()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
