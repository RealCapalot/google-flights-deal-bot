import time
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import os

class GoogleFlightsScraper:
    def __init__(self, headless=True, min_duration_hours=6, proxy_url=None, disable_images=True):
        """
        Initialize the Google Flights scraper.
        
        Args:
            headless (bool): Run browser in headless mode
            min_duration_hours (int): Minimum flight duration in hours to consider as "long flight"
            proxy_url (str): Proxy URL in format http://user:pass@host:port or http://host:port
            disable_images (bool): Whether to disable images for faster loading
        """
        self.min_duration_hours = min_duration_hours
        self.proxy_url = proxy_url
        self.disable_images = disable_images
        self.setup_browser(headless)
        self.logger = self.setup_logger()
    
    def setup_logger(self):
        """Configure logging"""
        logger = logging.getLogger('google_flights_scraper')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def setup_browser(self, headless):
        """Set up Selenium WebDriver"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Add proxy if specified
        if self.proxy_url:
            chrome_options.add_argument(f'--proxy-server={self.proxy_url}')
        
        # Disable images if requested
        if self.disable_images:
            chrome_prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", chrome_prefs)
        
        # Use the latest Chrome driver
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            # Fallback to installed Chrome
            service = Service(ChromeDriverManager(chrome_type=ChromeType.GOOGLE).install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set user agent to avoid detection
        self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {
            "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        })
        
        # Disable webdriver flags to avoid detection
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def search_flights(self, origin, destination, departure_date, return_date=None, max_wait=30):
        """
        Search for flights on Google Flights.
        
        Args:
            origin (str): Origin airport code
            destination (str): Destination airport code
            departure_date (str): Departure date in format YYYY-MM-DD
            return_date (str, optional): Return date in format YYYY-MM-DD
            max_wait (int): Maximum wait time in seconds for loading
            
        Returns:
            list: List of flight data dictionaries
        """
        try:
            # Construct URL for one-way or round trip
            if return_date:
                url = f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}%20from%20{origin}%20on%20{departure_date}%20through%20{return_date}"
            else:
                url = f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}%20from%20{origin}%20on%20{departure_date}"
            
            self.logger.info(f"Searching flights: {origin} to {destination} on {departure_date}")
            self.driver.get(url)
            
            # Wait for flights to load
            WebDriverWait(self.driver, max_wait).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[role='list'] > li"))
            )
            
            # Let the page load all dynamic content
            time.sleep(5)
            
            # Extract flights data
            return self._extract_flights_data()
            
        except Exception as e:
            self.logger.error(f"Error searching flights: {str(e)}")
            return []
    
    def _extract_flights_data(self):
        """Extract flight data from the loaded page"""
        flights = []
        
        try:
            # Find all flight cards
            flight_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='list'] > li")
            
            for flight_element in flight_elements:
                try:
                    # Extract price
                    price_element = flight_element.find_element(By.CSS_SELECTOR, "div[aria-label*='$']")
                    price_text = price_element.get_attribute("aria-label")
                    price = self._extract_price(price_text)
                    
                    # Extract airlines
                    airline_elements = flight_element.find_elements(By.CSS_SELECTOR, "div[aria-label*='Airline:']")
                    airlines = [el.get_attribute("aria-label").replace("Airline:", "").strip() for el in airline_elements]
                    
                    # Extract duration
                    duration_element = flight_element.find_element(By.CSS_SELECTOR, "div[aria-label*='Duration:']")
                    duration_text = duration_element.get_attribute("aria-label")
                    duration_hours = self._extract_duration_hours(duration_text)
                    
                    # Extract departure and arrival times
                    time_elements = flight_element.find_elements(By.CSS_SELECTOR, "div[aria-label*='Departure time:'], div[aria-label*='Arrival time:']")
                    departure_time = time_elements[0].get_attribute("aria-label").replace("Departure time:", "").strip()
                    arrival_time = time_elements[1].get_attribute("aria-label").replace("Arrival time:", "").strip()
                    
                    # Extract airports
                    airport_elements = flight_element.find_elements(By.CSS_SELECTOR, "div[aria-label*='Departing airport:'], div[aria-label*='Arrival airport:']")
                    departure_airport = airport_elements[0].get_attribute("aria-label").replace("Departing airport:", "").strip()
                    arrival_airport = airport_elements[1].get_attribute("aria-label").replace("Arrival airport:", "").strip()
                    
                    # Extract stops
                    stops_element = flight_element.find_element(By.CSS_SELECTOR, "div[aria-label*='stop']")
                    stops_text = stops_element.get_attribute("aria-label")
                    stops = 0 if "Nonstop" in stops_text else int(stops_text.split()[0])
                    
                    # Skip flights that are too short
                    if duration_hours < self.min_duration_hours:
                        continue
                    
                    # Create flight data dictionary
                    flight_data = {
                        "price": price,
                        "airlines": airlines,
                        "duration_hours": duration_hours,
                        "departure_time": departure_time,
                        "arrival_time": arrival_time, 
                        "departure_airport": departure_airport,
                        "arrival_airport": arrival_airport,
                        "stops": stops,
                        "price_per_hour": round(price / duration_hours, 2) if duration_hours > 0 else None
                    }
                    
                    flights.append(flight_data)
                    
                except Exception as e:
                    self.logger.warning(f"Error extracting flight data: {str(e)}")
            
            return flights
            
        except Exception as e:
            self.logger.error(f"Error extracting flights data: {str(e)}")
            return []
    
    def _extract_price(self, price_text):
        """Extract price value from price text"""
        try:
            # Extract digits and decimal point
            price_str = ''.join(c for c in price_text if c.isdigit() or c == '.')
            return float(price_str)
        except:
            return None
    
    def _extract_duration_hours(self, duration_text):
        """Extract duration in hours from duration text"""
        try:
            if "hr" in duration_text:
                hours_text = duration_text.split("hr")[0].strip().split()[-1]
                hours = int(hours_text)
                
                if "min" in duration_text:
                    mins_text = duration_text.split("min")[0].split("hr")[1].strip()
                    mins = int(mins_text) if mins_text else 0
                else:
                    mins = 0
                
                return hours + (mins / 60)
            return 0
        except:
            return 0
    
    def find_best_deals(self, flights, sort_by="price_per_hour", limit=10):
        """
        Find the best flight deals.
        
        Args:
            flights (list): List of flight dictionaries
            sort_by (str): Field to sort by (price, duration_hours, price_per_hour)
            limit (int): Maximum number of results to return
            
        Returns:
            list: Sorted list of best flight deals
        """
        if not flights:
            return []
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(flights)
        
        # Add value score (lower is better)
        if 'price_per_hour' in df.columns and not df['price_per_hour'].isnull().all():
            # Normalize price per hour (0-100 scale, lower is better)
            min_pph = df['price_per_hour'].min()
            max_pph = df['price_per_hour'].max()
            
            if min_pph != max_pph:
                df['value_score'] = 100 * (df['price_per_hour'] - min_pph) / (max_pph - min_pph)
            else:
                df['value_score'] = 50  # All same value
        
        # Sort by requested field
        if sort_by == "value_score" and "value_score" in df.columns:
            df = df.sort_values(by="value_score")  # Lower is better
        elif sort_by == "price_per_hour" and "price_per_hour" in df.columns:
            df = df.sort_values(by="price_per_hour")  # Lower is better
        elif sort_by == "price":
            df = df.sort_values(by="price")  # Lower is better
        elif sort_by == "duration_hours":
            df = df.sort_values(by="duration_hours", ascending=False)  # Higher is better
            
        # Return top results
        return df.head(limit).to_dict('records')
    
    def search_best_deals(self, origin, destination, departure_date, return_date=None, sort_by="price_per_hour", limit=10):
        """
        Search and find the best flight deals in one call.
        
        Args:
            origin (str): Origin airport code
            destination (str): Destination airport code
            departure_date (str): Departure date in format YYYY-MM-DD
            return_date (str, optional): Return date in format YYYY-MM-DD
            sort_by (str): Field to sort by (price, duration_hours, price_per_hour)
            limit (int): Maximum number of results to return
            
        Returns:
            list: Sorted list of best flight deals
        """
        flights = self.search_flights(origin, destination, departure_date, return_date)
        return self.find_best_deals(flights, sort_by, limit)
    
    def take_screenshot(self, filename=None):
        """
        Take a screenshot of the current browser window.
        
        Args:
            filename (str, optional): Custom filename, default is screenshot_TIMESTAMP.png
            
        Returns:
            str: Path to the saved screenshot
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        # Ensure the filename has .png extension
        if not filename.lower().endswith('.png'):
            filename += '.png'
        
        # Create screenshots directory if it doesn't exist
        screenshots_dir = 'screenshots'
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Save the screenshot
        filepath = os.path.join(screenshots_dir, filename)
        self.driver.save_screenshot(filepath)
        self.logger.info(f"Screenshot saved to {filepath}")
        
        return filepath
    
    def close(self):
        """Close the browser"""
        if hasattr(self, 'driver'):
            self.driver.quit() 