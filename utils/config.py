import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Selenium WebDriver Settings
HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
DISABLE_IMAGES = os.getenv('DISABLE_IMAGES', 'true').lower() == 'true'

# Scraper Settings
MIN_FLIGHT_DURATION_HOURS = int(os.getenv('MIN_FLIGHT_DURATION_HOURS', '6'))
DEFAULT_SORT_BY = os.getenv('DEFAULT_SORT_BY', 'price_per_hour')

# Search Parameters
DEFAULT_MIN_STAY_DAYS = int(os.getenv('DEFAULT_MIN_STAY_DAYS', '7'))
DEFAULT_MAX_STAY_DAYS = int(os.getenv('DEFAULT_MAX_STAY_DAYS', '14'))
DEFAULT_MONTHS_AHEAD = int(os.getenv('DEFAULT_MONTHS_AHEAD', '3'))

# Proxy Settings
USE_PROXY = os.getenv('USE_PROXY', 'false').lower() == 'true'
PROXY_HOST = os.getenv('PROXY_HOST', '')
PROXY_PORT = os.getenv('PROXY_PORT', '')
PROXY_USER = os.getenv('PROXY_USER', '')
PROXY_PASS = os.getenv('PROXY_PASS', '')

# Schedule Settings
DEFAULT_INTERVAL_HOURS = int(os.getenv('DEFAULT_INTERVAL_HOURS', '24'))

def get_proxy_url():
    """Get formatted proxy URL if proxy is enabled"""
    if not USE_PROXY or not PROXY_HOST or not PROXY_PORT:
        return None
        
    if PROXY_USER and PROXY_PASS:
        return f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    else:
        return f"http://{PROXY_HOST}:{PROXY_PORT}" 