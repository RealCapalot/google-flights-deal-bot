import time
import json
import logging
import pandas as pd
import re
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from selenium.webdriver.common.by import By

class GoogleFlightsScraper:
    def __init__(self, headless=True, min_duration_hours=6, proxy_url=None, disable_images=True, premium_only=False):
        """
        Initialize the Google Flights scraper.
        
        Args:
            headless (bool): Run browser in headless mode
            min_duration_hours (int): Minimum flight duration in hours to consider as "long flight"
            proxy_url (str): Proxy URL in format http://user:pass@host:port or http://host:port
            disable_images (bool): Whether to disable images for faster loading
            premium_only (bool): Only search for Business and First class flights
        """
        self.min_duration_hours = min_duration_hours
        self.proxy_url = proxy_url
        self.disable_images = disable_images
        self.premium_only = premium_only
        self.setup_browser(headless)
        self.logger = self.setup_logger()
        self.price_database = {}  # Track prices for discount comparison
    
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
        """Set up Selenium WebDriver with optimized settings"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # Optimized browser settings for speed
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        chrome_options.add_argument("--disable-site-isolation-trials")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=NetworkService")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Add proxy if specified
        if self.proxy_url:
            chrome_options.add_argument(f'--proxy-server={self.proxy_url}')
        
        # Disable images if requested
        if self.disable_images:
            chrome_prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", chrome_prefs)
        
        # Use Selenium Manager to handle driver installation
        try:
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.service import Service as ChromeService
            from webdriver_manager.chrome import ChromeDriverManager
            
            # Check if running in GitHub Actions
            if os.environ.get('GITHUB_ACTIONS'):
                # Use Chrome from GitHub Actions
                service = ChromeService()
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # Use ChromeDriverManager for local development
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            self.logger.error(f"Error setting up Chrome driver: {str(e)}")
            raise
        
        # Set user agent to avoid detection
        self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {
            "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        })
        
        # Disable webdriver flags to avoid detection
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Set page load timeout
        self.driver.set_page_load_timeout(30)  # 30 seconds timeout
    
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
            
            # Set to premium classes if requested
            if self.premium_only:
                try:
                    # Click on class selector
                    class_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "div[aria-label*='Cabin class']"))
                    )
                    class_button.click()
                    time.sleep(1)
                    
                    # Look for Business or First class options
                    premium_selectors = [
                        "div[aria-label*='Business']", 
                        "div[aria-label*='business']",
                        "div[aria-label*='Premium']", 
                        "div[aria-label*='premium']",
                        "div[aria-label*='First']",
                        "div[aria-label*='first']",
                        "div[aria-label*='Business class']",
                        "div[aria-label*='First class']",
                        "div[aria-label*='Premium economy']",
                        "div[aria-label*='Premium Economy']",
                        "div[aria-label*='Business Class']",
                        "div[aria-label*='First Class']"
                    ]
                    
                    premium_selected = False
                    for selector in premium_selectors:
                        try:
                            premium_option = WebDriverWait(self.driver, 3).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            premium_option.click()
                            self.logger.info(f"Selected premium cabin option: {selector}")
                            premium_selected = True
                            break
                        except:
                            continue
                    
                    if not premium_selected:
                        self.logger.warning("Could not find any premium cabin options")
                    
                    # Click the Done button
                    try:
                        done_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label*='Done']"))
                        )
                        done_button.click()
                        time.sleep(3)  # Wait for results to update
                    except Exception as e:
                        self.logger.warning(f"Could not click Done button: {str(e)}")
                except Exception as e:
                    self.logger.warning(f"Could not select premium class: {str(e)}")
            
            # Extract flights data
            return self._extract_flights_data(origin, destination, departure_date, return_date)
            
        except Exception as e:
            # Capture d'écran automatique en cas d'erreur
            screenshot_name = f"error_{origin}_{destination}_{departure_date}.png"
            self.driver.save_screenshot(screenshot_name)
            self.logger.error(f"Screenshot saved for error: {screenshot_name}")
            self.logger.exception("Error searching flights:")
            import sys
            sys.exit(1)
            return []
    
    def _extract_flights_data(self, origin, destination, departure_date, return_date=None):
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
                    
                    # Extract cabin class
                    cabin_class = "Economy"  # Default
                    try:
                        cabin_elements = flight_element.find_elements(By.CSS_SELECTOR, "div[aria-label*='class']")
                        if cabin_elements:
                            cabin_text = cabin_elements[0].get_attribute("aria-label")
                            if "business" in cabin_text.lower():
                                cabin_class = "Business"
                            elif "first" in cabin_text.lower():
                                cabin_class = "First"
                            elif "premium" in cabin_text.lower():
                                cabin_class = "Premium Economy"
                    except:
                        pass
                    
                    # Skip if not premium and premium_only is enabled
                    if self.premium_only and cabin_class == "Economy":
                        continue
                    
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
                    
                    # Calculate the route key for price tracking
                    route_key = f"{origin}-{destination}-{cabin_class}"
                    
                    # Check if this is a good deal by comparing to historical prices
                    is_good_deal, discount_pct = self._check_if_good_deal(route_key, price)
                    
                    # Create flight data dictionary
                    flight_data = {
                        "price": price,
                        "cabin_class": cabin_class,
                        "airlines": airlines,
                        "duration_hours": duration_hours,
                        "departure_time": departure_time,
                        "arrival_time": arrival_time, 
                        "departure_airport": departure_airport,
                        "arrival_airport": arrival_airport,
                        "stops": stops,
                        "price_per_hour": round(price / duration_hours, 2) if duration_hours > 0 else None,
                        "is_good_deal": is_good_deal,
                        "discount_percentage": discount_pct
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
    
    def _check_if_good_deal(self, route_key, current_price):
        """
        Check if the current price is a good deal by comparing to average prices
        
        Args:
            route_key (str): Route identifier in format "origin-destination-cabin_class"
            current_price (float): Current price to check
        
        Returns:
            tuple: (is_good_deal, discount_percentage)
        """
        # Initialize prices for this route if not already tracked
        if route_key not in self.price_database:
            try:
                # Try to get baseline prices for this route from file
                if os.path.exists('price_database.json'):
                    with open('price_database.json', 'r') as f:
                        stored_prices = json.load(f)
                        if route_key in stored_prices:
                            self.price_database[route_key] = stored_prices[route_key]
                        else:
                            # Initialize with slightly higher than current price to be conservative
                            self.price_database[route_key] = {
                                "min_price": current_price,
                                "max_price": current_price * 1.5,
                                "avg_price": current_price * 1.3,
                                "count": 1,
                                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                                "prices": [current_price],  # Store historical prices
                                "seasonal_factors": {},  # Store seasonal price factors
                                "last_month_avg": current_price,  # Last 30 days average
                                "last_week_avg": current_price,  # Last 7 days average
                                "price_trend": "stable"  # Price trend: increasing, decreasing, stable
                            }
                else:
                    # Initialize with slightly higher than current price to be conservative
                    self.price_database[route_key] = {
                        "min_price": current_price,
                        "max_price": current_price * 1.5,
                        "avg_price": current_price * 1.3,
                        "count": 1,
                        "last_updated": datetime.now().strftime("%Y-%m-%d"),
                        "prices": [current_price],  # Store historical prices
                        "seasonal_factors": {},  # Store seasonal price factors
                        "last_month_avg": current_price,  # Last 30 days average
                        "last_week_avg": current_price,  # Last 7 days average
                        "price_trend": "stable"  # Price trend: increasing, decreasing, stable
                    }
            except Exception as e:
                self.logger.error(f"Error initializing price database: {str(e)}")
                # Initialize with default values
                self.price_database[route_key] = {
                    "min_price": current_price,
                    "max_price": current_price * 1.5,
                    "avg_price": current_price * 1.3,
                    "count": 1,
                    "last_updated": datetime.now().strftime("%Y-%m-%d"),
                    "prices": [current_price],
                    "seasonal_factors": {},
                    "last_month_avg": current_price,
                    "last_week_avg": current_price,
                    "price_trend": "stable"
                }
        
        # Get the price data for this route
        price_data = self.price_database[route_key]
        
        # Update price statistics
        price_data["min_price"] = min(price_data["min_price"], current_price)
        price_data["max_price"] = max(price_data["max_price"], current_price)
        
        # Update historical prices (keep last 100 prices)
        price_data["prices"].append(current_price)
        if len(price_data["prices"]) > 100:
            price_data["prices"] = price_data["prices"][-100:]
        
        # Update average price (exponential moving average)
        alpha = 0.1  # Smoothing factor
        price_data["avg_price"] = (alpha * current_price) + ((1 - alpha) * price_data["avg_price"])
        
        # Update last month and week averages
        if len(price_data["prices"]) >= 30:
            price_data["last_month_avg"] = sum(price_data["prices"][-30:]) / 30
        if len(price_data["prices"]) >= 7:
            price_data["last_week_avg"] = sum(price_data["prices"][-7:]) / 7
        
        # Update price trend
        if len(price_data["prices"]) >= 3:
            last_3_prices = price_data["prices"][-3:]
            if last_3_prices[0] < last_3_prices[1] < last_3_prices[2]:
                price_data["price_trend"] = "increasing"
            elif last_3_prices[0] > last_3_prices[1] > last_3_prices[2]:
                price_data["price_trend"] = "decreasing"
            else:
                price_data["price_trend"] = "stable"
        
        # Update seasonal factors (by month)
        current_month = datetime.now().month
        if current_month not in price_data["seasonal_factors"]:
            price_data["seasonal_factors"][current_month] = []
        price_data["seasonal_factors"][current_month].append(current_price)
        
        # Keep only last 3 years of seasonal data
        for month in list(price_data["seasonal_factors"].keys()):
            if len(price_data["seasonal_factors"][month]) > 3:
                price_data["seasonal_factors"][month] = price_data["seasonal_factors"][month][-3:]
        
        # Calculate seasonal average for current month
        if current_month in price_data["seasonal_factors"] and price_data["seasonal_factors"][current_month]:
            seasonal_avg = sum(price_data["seasonal_factors"][current_month]) / len(price_data["seasonal_factors"][current_month])
        else:
            seasonal_avg = price_data["avg_price"]
        
        # Update count and last updated
        price_data["count"] += 1
        price_data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        
        # Save updated prices
        self._save_price_database()
        
        # Calculate discount percentages from different baselines
        avg_discount = round(((price_data["avg_price"] - current_price) / price_data["avg_price"]) * 100, 2)
        month_discount = round(((price_data["last_month_avg"] - current_price) / price_data["last_month_avg"]) * 100, 2)
        week_discount = round(((price_data["last_week_avg"] - current_price) / price_data["last_week_avg"]) * 100, 2)
        seasonal_discount = round(((seasonal_avg - current_price) / seasonal_avg) * 100, 2)
        
        # Use the highest discount percentage
        discount_pct = max(avg_discount, month_discount, week_discount, seasonal_discount)
        
        # Adjust threshold based on price trend
        base_threshold = 35  # Base threshold for good deals
        if price_data["price_trend"] == "increasing":
            # Lower threshold when prices are trending up
            threshold = base_threshold - 5
        elif price_data["price_trend"] == "decreasing":
            # Higher threshold when prices are trending down
            threshold = base_threshold + 5
        else:
            threshold = base_threshold
        
        # Check if price represents a good deal
        is_good_deal = discount_pct >= threshold
        
        return is_good_deal, discount_pct
    
    def _save_price_database(self):
        """Save the price database to a file"""
        try:
            with open('price_database.json', 'w') as f:
                json.dump(self.price_database, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving price database: {str(e)}")
    
    def find_best_deals(self, flights, sort_by="price_per_hour", limit=10, discount_threshold=35):
        """
        Find the best flight deals.
        
        Args:
            flights (list): List of flight dictionaries
            sort_by (str): Field to sort by (price, duration_hours, price_per_hour, discount_percentage)
            limit (int): Maximum number of results to return
            discount_threshold (float): Minimum discount percentage to consider (for good deals)
            
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
        
        # Filter to only good deals if requested
        if discount_threshold > 0:
            if 'discount_percentage' in df.columns:
                df = df[df['discount_percentage'] >= discount_threshold]
        
        if df.empty:
            return []
        
        # Sort by requested field
        if sort_by == "value_score" and "value_score" in df.columns:
            df = df.sort_values(by="value_score")  # Lower is better
        elif sort_by == "price_per_hour" and "price_per_hour" in df.columns:
            df = df.sort_values(by="price_per_hour")  # Lower is better
        elif sort_by == "price":
            df = df.sort_values(by="price")  # Lower is better
        elif sort_by == "duration_hours":
            df = df.sort_values(by="duration_hours", ascending=False)  # Higher is better
        elif sort_by == "discount_percentage" and "discount_percentage" in df.columns:
            df = df.sort_values(by="discount_percentage", ascending=False)  # Higher is better
            
        # Return top results
        return df.head(limit).to_dict('records')
    
    def search_best_deals(self, origin, destination, departure_date, return_date=None, sort_by="price_per_hour", limit=10, discount_threshold=35):
        """
        Search and find the best flight deals in one call.
        
        Args:
            origin (str): Origin airport code
            destination (str): Destination airport code
            departure_date (str): Departure date in format YYYY-MM-DD
            return_date (str, optional): Return date in format YYYY-MM-DD
            sort_by (str): Field to sort by (price, duration_hours, price_per_hour, discount_percentage)
            limit (int): Maximum number of results to return
            discount_threshold (float): Minimum discount percentage to consider (for good deals)
            
        Returns:
            list: Sorted list of best flight deals
        """
        flights = self.search_flights(origin, destination, departure_date, return_date)
        return self.find_best_deals(flights, sort_by, limit, discount_threshold)
    
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
    
    def export_to_csv(self, flights, filename=None):
        """
        Export flights data to CSV file.
        
        Args:
            flights (list): List of flight dictionaries
            filename (str, optional): Custom filename, default is flights_TIMESTAMP.csv
            
        Returns:
            str: Path to the saved CSV file
        """
        if not flights:
            self.logger.warning("No flights data to export")
            return None
            
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"flights_{timestamp}.csv"
        
        # Ensure the filename has .csv extension
        if not filename.lower().endswith('.csv'):
            filename += '.csv'
        
        # Create exports directory if it doesn't exist
        exports_dir = 'exports'
        os.makedirs(exports_dir, exist_ok=True)
        
        # Save the CSV
        filepath = os.path.join(exports_dir, filename)
        
        # Convert to DataFrame and export
        df = pd.DataFrame(flights)
        
        # Handle lists in the airlines column
        if 'airlines' in df.columns:
            df['airlines'] = df['airlines'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
            
        df.to_csv(filepath, index=False)
        self.logger.info(f"Flights data exported to {filepath}")
        
        return filepath
    
    def export_to_json(self, flights, filename=None):
        """
        Export flights data to JSON file.
        
        Args:
            flights (list): List of flight dictionaries
            filename (str, optional): Custom filename, default is flights_TIMESTAMP.json
            
        Returns:
            str: Path to the saved JSON file
        """
        if not flights:
            self.logger.warning("No flights data to export")
            return None
            
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"flights_{timestamp}.json"
        
        # Ensure the filename has .json extension
        if not filename.lower().endswith('.json'):
            filename += '.json'
        
        # Create exports directory if it doesn't exist
        exports_dir = 'exports'
        os.makedirs(exports_dir, exist_ok=True)
        
        # Save the JSON
        filepath = os.path.join(exports_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(flights, f, indent=4)
        
        self.logger.info(f"Flights data exported to {filepath}")
        
        return filepath
    
    def get_multiple_date_options(self, origin, destination, start_date, num_days=100, return_trip=False, days_between=7, max_workers=10):
        """
        Search for flights across multiple dates using parallel processing.
        
        Args:
            origin (str): Origin airport code
            destination (str): Destination airport code
            start_date (str): Start date in format YYYY-MM-DD
            num_days (int): Number of departure dates to check
            return_trip (bool): Whether to include return flights
            days_between (int): For return trips, days between departure and return
            max_workers (int): Maximum number of parallel workers
            
        Returns:
            dict: Dictionary with dates as keys and flight lists as values
        """
        results = {}
        start = datetime.strptime(start_date, "%Y-%m-%d")
        dates_to_search = []
        
        # Generate all dates to search
        for i in range(num_days):
            current_date = start + timedelta(days=i)
            departure_date = current_date.strftime("%Y-%m-%d")
            return_date = None
            if return_trip:
                return_date = (current_date + timedelta(days=days_between)).strftime("%Y-%m-%d")
            dates_to_search.append((departure_date, return_date))
        
        # Function to search a single date
        def search_single_date(date_info):
            departure_date, return_date = date_info
            try:
                self.logger.info(f"Searching date: {departure_date}")
                flights = self.search_flights(origin, destination, departure_date, return_date)
                return departure_date, flights
            except Exception as e:
                self.logger.error(f"Error searching date {departure_date}: {str(e)}")
                return departure_date, []
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_date = {
                executor.submit(search_single_date, date_info): date_info 
                for date_info in dates_to_search
            }
            
            # Process results as they complete
            for future in tqdm(as_completed(future_to_date), total=len(dates_to_search), desc="Searching dates"):
                date_info = future_to_date[future]
                try:
                    departure_date, flights = future.result()
                    results[departure_date] = flights
                except Exception as e:
                    self.logger.error(f"Error processing results for date {date_info[0]}: {str(e)}")
        
        return results
    
    def retry_with_backoff(self, func, max_retries=3, initial_delay=2):
        """
        Retry a function with exponential backoff.
        
        Args:
            func: Function to retry
            max_retries (int): Maximum number of retry attempts
            initial_delay (int): Initial delay in seconds
            
        Returns:
            Any: Result of the function call or None if all retries fail
        """
        retries = 0
        delay = initial_delay
        
        while retries < max_retries:
            try:
                return func()
            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    self.logger.error(f"Maximum retries reached. Last error: {str(e)}")
                    return None
                
                self.logger.warning(f"Retry {retries}/{max_retries}. Error: {str(e)}")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
    
    def close(self):
        """Close the browser"""
        if hasattr(self, 'driver'):
            self.driver.quit() 