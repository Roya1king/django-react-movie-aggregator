import json
import requests
import time
import urllib.parse
from bs4 import BeautifulSoup

from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# --- Selenium Imports ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
# --- Imports for Smart Wait ---
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.keys import Keys

# --- Stealth Import ---
try:
    from selenium_stealth import stealth
except ImportError:
    print("[Task] selenium-stealth not installed, proceeding without it.")
    stealth = None

from .models import SiteSource

# This is the advanced stealth script
stealth_js = r"""
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
if (!window.chrome) { window.chrome = { runtime: {} }; }
try {
  const orig = navigator.permissions && navigator.permissions.query;
  if (orig) {
    navigator.permissions.__proto__.query = function(p) {
      if (p && p.name === 'notifications') {
        return Promise.resolve({ state: Notification.permission });
      }
      return orig(p);
    };
  }
} catch(e) {}
try {
  const origGetContext = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function(type) {
    const ctx = origGetContext.apply(this, arguments);
    try {
      if ((type === 'webgl' || type === 'experimental-webgl') && ctx && ctx.getParameter) {
        const origGetParameter = ctx.getParameter.bind(ctx);
        ctx.getParameter = function(param) {
          if (param === 37445) return "Intel Inc.";
          if (param === 37446) return "Intel Iris OpenGL Engine";
          return origGetParameter(param);
        };
      }
    } catch(e){}
    return ctx;
  };
} catch(e){}
"""

def get_page_html(site, search_term):
    """
    Fetches the HTML content from the target site.
    Uses Selenium if required, otherwise uses requests.
    """
    
    if site.requires_playwright: # Kept var name for simplicity
        print(f"[Task] Using Selenium for: {site.name}")
        search_term_encoded = urllib.parse.quote(search_term)
        url = (site.base_url.rstrip('/') + site.search_endpoint).replace("%QUERY%", search_term_encoded)
        
        driver = None
        html = None
        try:
            options = Options()
            options.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
            options.page_load_strategy = 'eager'
            
            # Use your "warmed up" dedicated profile
            options.add_argument(r"user-data-dir=C:\Users\Dell\BraveSeleniumProfile")
            
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--log-level=3")
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
            
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Apply stealth patches
            if stealth:
                try:
                    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
                except Exception as e:
                    print(f"[Stealth] selenium_stealth call failed: {e}")
            try:
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": stealth_js})
            except Exception as e:
                print(f"[CDP] addScriptToEvaluateOnNewDocument failed: {e}")

            
            driver.set_page_load_timeout(10) # 30 second timeout
            
            print(f"[Selenium] Navigating to: {url}")
            try:
                driver.get(url)
            except TimeoutException:
                print("[Selenium] Page load timed out (eager). This is normal. Proceeding...")
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)

            # --- THIS IS THE FIX ---
            # Wait for the *dynamic* result container from your database
            wait = WebDriverWait(driver, 20) # Wait up to 20 seconds
            print(f"[Selenium] Waiting for movie items ('{site.result_container_selector}') to appear...")
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, site.result_container_selector))
            )
            print("[Selenium] Movie items found!")
            # --- END FIX ---
            
            html = driver.page_source
            print("[Selenium] Page source retrieved.")

        except WebDriverException as e:
            if "user data directory is already in use" in str(e):
                print("[FATAL SELENIUM ERROR] You must CLOSE all your manual Brave browser windows before running the script!")
                html = None
            else:
                print(f"[Selenium WebDriver Error] {e}")
                html = None 
        except Exception as e:
            print(f"[Selenium Unexpected Error] {e}")
            html = None
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass 
        return html
    
    # --- Standard Requests (No Playwright) ---
    
    if site.search_type == 'GET':
        print(f"[Task] Using GET for: {site.name}")
        search_term_encoded = urllib.parse.quote(search_term)
        url = (site.base_url.rstrip('/') + site.search_endpoint).replace("%QUERY%", search_term_encoded)
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            return response.text
        except Exception as e:
            print(f"[GET Error] {e}")
            return None

    if site.search_type == 'POST':
        print(f"[Task] Using POST for: {site.name}")
        url = site.base_url.rstrip('/') + site.search_endpoint
        
        payload_str = (site.post_payload_template or "").replace("%QUERY%", search_term)
        
        try:
            payload_data = json.loads(payload_str)
            response = requests.post(url, json=payload_data, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        except json.JSONDecodeError:
            try:
                payload_data = {}
                for line in payload_str.split('\n'):
                    if ':' in line:
                        key, val = line.split(':', 1)
                        payload_data[key.strip()] = val.strip()
                    elif '=' in line:
                         key, val = line.split('=', 1)
                         payload_data[key.strip()] = val.strip()

                if not payload_data:
                        raise ValueError("Payload is not JSON and not valid key-value pairs.")

                print(f"[Task] Sending POST with form-data: {payload_data}")
                response = requests.post(url, data=payload_data, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            
            except Exception as e:
                print(f"[POST Payload Error] {e}")
                return None
        except Exception as e:
            print(f"[POST Request Error] {e}")
            return None

        try:
            json_response = response.json()
            if 'data' in json_response and 'results' in json_response['data']:
                return json_response['data']['results'] 
            else:
                return response.text 
        except (json.JSONDecodeError, requests.exceptions.JSONDecodeError):
            return response.text 

    return None

@shared_task
def scrape_site(site_id, search_term, channel_name):
    """
    The main Celery task to scrape a single site and send
    results back over the WebSocket.
    """
    channel_layer = get_channel_layer()
    
    try:
        site = SiteSource.objects.get(id=site_id)
    except SiteSource.DoesNotExist:
        return
    
    html = get_page_html(site, search_term)

    if not html:
        async_to_sync(channel_layer.send)(channel_name, {
            'type': 'send_error_message', 
            'message': f"Failed to fetch data from {site.name}"
        })
        return

    soup = BeautifulSoup(html, 'html.parser')
    
    containers = soup.select(site.result_container_selector)

    if not containers:
        print(f"[Task] No containers found for {site.name} with selector '{site.result_container_selector}'")

    for item in containers:
        try:
            title_tag = item.select_one(site.result_title_selector)
            link_tag = item.select_one(site.result_link_selector)
            poster_tag = item.select_one(site.result_poster_selector)

            if not all([title_tag, link_tag, poster_tag]):
                continue

            title = title_tag.text.strip()
            link = link_tag['href']
            poster = poster_tag[site.result_poster_attribute]

            if not link.startswith('http'):
                link = urllib.parse.urljoin(site.base_url, link)
            if not poster.startswith('http'):
                poster = urllib.parse.urljoin(site.base_url, poster)

            result = {
                'source': site.name,
                'title': title,
                'link': link,
                'poster': poster,
            }

            async_to_sync(channel_layer.send)(channel_name, {
                'type': 'send_search_result', 
                'result': result
            })

        except Exception as e:
            print(f"[Parsing Error] Failed to parse item from {site.name}: {e}")
            continue

    print(f"[Task] Finished scraping: {site.name}")