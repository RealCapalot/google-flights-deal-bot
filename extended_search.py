#!/usr/bin/env python3
"""
Extended Google Flights Search - Search up to 500 days in advance
Searches for flights across a very long date range and sends results to email
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime, timedelta

import os.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from origin_filter import filter_routes
except ImportError:
    def filter_routes(routes, origins):
        """Default filter if module not found"""
        if not origins:
            return routes
        origins = origins.split(",")
        return [r for r in routes if r["origin"] in origins]

from scrapers.flights_scraper import GoogleFlightsScraper
from scrapers.email_sender import EmailSender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extended_search.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("extended_search")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Extended Google Flights Search (up to 500 days)")
    
    # Route configuration
    parser.add_argument("--routes-file", default="routes.json", help="JSON file containing routes to check")
    parser.add_argument("--cdg-only", action="store_true", help="Only search routes originating from CDG")
    parser.add_argument("--origin-filter", help="Filter by origin airports (comma-separated)")
    
    # Email settings
    parser.add_argument("--email", default="alec.dc29@gmail.com", help="Email address to send notifications to")
    parser.add_argument("--email-sender", help="Sender email address")
    parser.add_argument("--email-password", help="Sender email password")
    
    # Time range settings
    parser.add_argument("--max-days", type=int, default=500, help="Maximum days into the future to search")
    parser.add_argument("--start-days", type=int, default=1, help="Start checking from X days in the future")
    parser.add_argument("--check-interval", type=int, default=7, help="Check every X days in the date range")
    
    # Stay duration settings
    parser.add_argument("--min-stay", type=int, default=3, help="Minimum stay duration in days")
    parser.add_argument("--max-stay", type=int, default=21, help="Maximum stay duration in days")
    parser.add_argument("--stay-interval", type=int, default=2, help="Interval between stay durations to check")
    
    # Search settings
    parser.add_argument("--premium-only", action="store_true", help="Only search for business and first class")
    parser.add_argument("--min-duration", type=float, default=6.0, help="Minimum flight duration hours")
    parser.add_argument("--limit", type=int, default=5, help="Number of results per route to save")
    parser.add_argument("--export", action="store_true", help="Export results to CSV and JSON")
    parser.add_argument("--discount-threshold", type=float, default=35.0, 
                        help="Minimum discount percentage to consider as a good deal")
    
    # Runtime settings
    parser.add_argument("--batch-size", type=int, default=10, help="Number of searches to run before taking a break")
    parser.add_argument("--batch-pause", type=int, default=60, help="Seconds to pause between batches")
    parser.add_argument("--search-pause", type=int, default=3, help="Seconds to pause between searches")
    
    args = parser.parse_args()
    return args

def load_routes(routes_file, cdg_only=False):
    """Load routes from a JSON file"""
    if not os.path.exists(routes_file):
        logger.error(f"Routes file not found: {routes_file}")
        return []
    
    try:
        with open(routes_file, 'r') as f:
            routes = json.load(f)
        
        # Filter for CDG routes only if requested
        if cdg_only:
            routes = [r for r in routes if r["origin"] == "CDG"]
        
        # Apply origin filter if specified
        if args.origin_filter:
            routes = filter_routes(routes, args.origin_filter)
            
        logger.info(f"Loaded {len(routes)} routes from {routes_file}")
        return routes
    except Exception as e:
        logger.error(f"Error loading routes file: {str(e)}")
        return []

def generate_extended_dates(start_days, max_days, check_interval):
    """Generate a list of dates to check over an extended period"""
    start_date = datetime.now() + timedelta(days=start_days)
    end_date = datetime.now() + timedelta(days=max_days)
    
    dates = []
    current_date = start_date
    
    while current_date <= end_date:
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=check_interval)
    
    logger.info(f"Generated {len(dates)} dates from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    return dates

def generate_smart_date_pairs(dates, min_stay, max_stay, stay_interval):
    """Generate smart date pairs for optimal coverage of the extended period"""
    date_pairs = []
    
    # Process dates to create departure-return pairs
    for i, dep_date_str in enumerate(dates):
        dep_date = datetime.strptime(dep_date_str, "%Y-%m-%d")
        
        # Create varying length stays at different intervals
        for stay_length in range(min_stay, max_stay + 1, stay_interval):
            ret_date = dep_date + timedelta(days=stay_length)
            
            # Skip if return date is beyond our maximum search window
            max_date = datetime.now() + timedelta(days=500)
            if ret_date > max_date:
                continue
                
            ret_date_str = ret_date.strftime("%Y-%m-%d")
            date_pairs.append((dep_date_str, ret_date_str))
    
    logger.info(f"Generated {len(date_pairs)} date pairs with stays from {min_stay} to {max_stay} days")
    return date_pairs

def run_extended_search(scraper, email_sender, search_params):
    """
    Run extended search across multiple routes and dates
    
    Args:
        scraper: GoogleFlightsScraper instance
        email_sender: EmailSender instance
        search_params: Dictionary of search parameters
    """
    try:
        # Load routes
        with open(search_params['routes_file'], 'r') as f:
            routes_data = json.load(f)
        
        if not routes_data or 'routes' not in routes_data:
            logger.error("No routes found in routes file")
            return
        
        routes = routes_data['routes']
        logger.info(f"Loaded {len(routes)} routes to search")
        
        # Get current date and calculate end date
        start_date = datetime.now()
        end_date = start_date + timedelta(days=search_params['max_days'])
        
        # Search each route
        for route in routes:
            origin = route['origin']
            destination = route['destination']
            
            logger.info(f"Searching route: {origin} to {destination}")
            
            # Search for each stay duration
            for stay_days in range(search_params['min_stay'], search_params['max_stay'] + 1):
                # Search for each departure date
                current_date = start_date
                while current_date <= end_date:
                    departure_date = current_date.strftime("%Y-%m-%d")
                    return_date = (current_date + timedelta(days=stay_days)).strftime("%Y-%m-%d")
                    
                    logger.info(f"Searching dates: {departure_date} to {return_date} (stay: {stay_days} days)")
                    
                    # Search for flights
                    flights = scraper.search_flights(
                        origin=origin,
                        destination=destination,
                        departure_date=departure_date,
                        return_date=return_date
                    )
                    
                    # Find best deals
                    best_deals = scraper.find_best_deals(
                        flights=flights,
                        sort_by="price_per_hour",
                        limit=5,
                        discount_threshold=search_params['discount_threshold']
                    )
                    
                    # If good deals found, send email
                    if best_deals:
                        logger.info(f"Found {len(best_deals)} good deals for {origin}-{destination}")
                        
                        # Take screenshot
                        screenshot_path = scraper.take_screenshot(
                            f"{origin}_{destination}_{departure_date}_{return_date}.png"
                        )
                        
                        # Export to CSV
                        csv_path = scraper.export_to_csv(
                            best_deals,
                            f"{origin}_{destination}_{departure_date}_{return_date}.csv"
                        )
                        
                        # Send email
                        email_sender.send_flight_deals(
                            origin=origin,
                            destination=destination,
                            departure_date=departure_date,
                            return_date=return_date,
                            deals=best_deals,
                            screenshot_path=screenshot_path,
                            csv_path=csv_path
                        )
                    
                    # Move to next date (check every 7 days)
                    current_date += timedelta(days=7)
                    
                    # Pause between searches
                    time.sleep(3)
            
            # Pause between routes
            time.sleep(5)
            
    except Exception as e:
        logger.error(f"Error in extended search: {str(e)}")
        raise

def main():
    """Main function"""
    global args
    args = parse_args()
    run_extended_search(args)

if __name__ == "__main__":
    main() 