# File: backend/scraper_api/tasks.py

import json
import urllib.parse
import requests
from bs4 import BeautifulSoup

from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import SiteSource

# --- THIS IS THE NEW FLARESOLVERR FUNCTION ---
def get_page_html_with_flaresolverr(url: str, site_name: str) -> str:
    """
    Uses FlareSolverr to bypass Cloudflare and get the HTML.
    """
    print(f"[Task] Using FlareSolverr for: {site_name}")
    
    # FlareSolverr's API endpoint
    flaresolverr_url = "http://localhost:8191/v1"
    
    # The payload FlareSolverr expects
    payload = {
        'cmd': 'request.get',
        'url': url,
        'maxTimeout': 60000  # 60 second timeout
    }
    
    try:
        # Make a POST request to FlareSolverr
        response = requests.post(flaresolverr_url, json=payload)
        response.raise_for_status() # Raise an error for bad status
        
        data = response.json()
        
        if data.get('status') == 'ok':
            print(f"[Task] FlareSolverr succeeded for: {site_name}")
            return data['solution']['response']
        else:
            print(f"[Task] FlareSolverr failed for: {site_name}. Status: {data.get('status')}")
            print(f"[Task] Message: {data.get('message')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"[Task] Failed to connect to FlareSolverr: {e}")
        print("[Task] Is FlareSolverr running in Docker?")
        return None
# --- END FLARESOLVERR FUNCTION ---


def get_page_html(site, search_term):
    """
    Fetches the HTML content from the target site.
    Uses FlareSolverr if required, otherwise uses requests.
    """
    search_query = urllib.parse.quote(search_term)
    
    # The 'requires_playwright' checkbox now means "requires_flaresolverr"
    if site.requires_playwright:
        url = (site.base_url.rstrip('/') + site.search_endpoint).replace("%QUERY%", search_query)
        return get_page_html_with_flaresolverr(url, site.name)

    
    # --- Standard Requests (No Playwright) ---
    # (This section is for your simple sites like Vegamovies)
    
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