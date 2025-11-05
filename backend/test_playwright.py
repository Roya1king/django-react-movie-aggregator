from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)  # set headless=False to see the browser window
    page = browser.new_page()
    page.goto("https://www.wikipedia.org")
    print("Page title:", page.title())
    print("Page URL:", page.url)
    browser.close()
