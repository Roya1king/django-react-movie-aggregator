import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth

# --- This is your NEW profile path ---
PROFILE_PATH = r"C:\Users\Dell\BraveSeleniumProfile"
BRAVE_EXE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

print("Starting Brave to train your profile...")
print(f"Profile path: {PROFILE_PATH}")
print("\n--- WHAT TO DO ---")
print("1. A Brave window will open.")
print("2. LOG IN TO GOOGLE. This is the most important step.")
print("3. Visit a few normal sites (Wikipedia, news, etc.).")
print("4. Go to hdhub4u and vegamovies.")
print("5. Solve the Cloudflare CAPTCHA one time.")
print("6. When you are done, close the browser and stop this script (CTRL+C).")
print("\nYour profile is now 'warmed up'!")
print("Starting in 10 seconds...")
time.sleep(10)

driver = None
try:
    options = Options()
    options.binary_location = BRAVE_EXE_PATH
    options.add_argument(f"user-data-dir={PROFILE_PATH}") # Use the new profile
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Apply stealth
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)

    # Start at a neutral, trusted site
    driver.get("https://google.com")

    # Keep the browser open until you manually close it or stop the script
    print("\nBrowser is open. Start training! (Press CTRL+C here to quit)")
    while True:
        time.sleep(60)

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if driver:
        driver.quit()
    print("Training session complete.")
