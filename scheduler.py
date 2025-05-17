import os
import time
import json
import schedule
import logging
import argparse
from datetime import datetime

from scrapers.flights_scraper import GoogleFlightsScraper
from utils.date_utils import get_next_n_months_date_range, generate_date_pairs
from utils.config import get_proxy_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("scheduler")

def load_routes(routes_file):
    """Load routes configuration from JSON file"""
    try:
        with open(routes_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading routes file: {str(e)}")
        return []

def scrape_route(route, months_ahead=3, min_duration=6, min_stay=7, max_stay=14, 
                sort_by="price_per_hour", limit=20, headless=True, use_proxy=False, 
                disable_images=True, take_screenshots=False):
    """Scrape a single route and save results"""
    origin = route["origin"]
    destination = route["destination"]
    
    # Get date range
    start_date, end_date = get_next_n_months_date_range(months_ahead)
    
    # Get proxy URL if enabled
    proxy_url = get_proxy_url() if use_proxy else None
    
    # Initialize scraper
    scraper = GoogleFlightsScraper(
        headless=headless, 
        min_duration_hours=min_duration,
        proxy_url=proxy_url,
        disable_images=disable_images
    )
    
    try:
        # Generate date pairs for round trips
        date_pairs = generate_date_pairs(
            start_date, 
            end_date, 
            trip_min_days=min_stay, 
            trip_max_days=max_stay
        )
        
        logger.info(f"Searching for flights: {origin} to {destination}")
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(f"Generated {len(date_pairs)} date pairs to search")
        
        all_results = []
        
        for departure_date, return_date in date_pairs:
            try:
                results = scraper.search_flights(
                    origin, 
                    destination, 
                    departure_date,
                    return_date
                )
                
                if take_screenshots:
                    screenshot_name = f"{origin}_to_{destination}_{departure_date}_to_{return_date}.png"
                    scraper.take_screenshot(screenshot_name)
                
                if results:
                    # Add dates to results
                    for result in results:
                        result["departure_date"] = departure_date
                        result["return_date"] = return_date
                    
                    all_results.extend(results)
                
                # Wait between requests
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error scraping {origin} to {destination} on {departure_date}-{return_date}: {str(e)}")
        
        # Find best deals
        best_deals = scraper.find_best_deals(all_results, sort_by, limit)
        
        # Save results
        if best_deals:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{origin}_to_{destination}_{timestamp}"
            
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Save as JSON
            json_path = os.path.join('data', f"{filename}.json")
            with open(json_path, 'w') as f:
                json.dump(best_deals, f, indent=2)
            
            logger.info(f"Found {len(best_deals)} deals for {origin} to {destination}")
            logger.info(f"Saved results to {json_path}")
            
            # Log the top 3 best deals
            if len(best_deals) > 0:
                logger.info(f"Top 3 deals for {origin} to {destination}:")
                for i, deal in enumerate(best_deals[:3]):
                    logger.info(f"#{i+1}: ${deal['price']} - {deal['airlines']} - {deal['departure_date']} to {deal['return_date']}")
        else:
            logger.warning(f"No deals found for {origin} to {destination}")
        
    except Exception as e:
        logger.error(f"Error processing route {origin} to {destination}: {str(e)}")
    finally:
        scraper.close()

def run_scheduled_scraper(routes_file, job_interval=24, **kwargs):
    """Run the scheduled scraper job"""
    logger.info(f"Starting scheduled scraper job, will run every {job_interval} hours")
    
    def job():
        logger.info("Running scheduled scraper job")
        routes = load_routes(routes_file)
        
        if not routes:
            logger.error("No routes found or error loading routes file")
            return
        
        logger.info(f"Found {len(routes)} routes to scrape")
        
        for route in routes:
            scrape_route(route, **kwargs)
    
    # Run once immediately
    job()
    
    # Schedule to run every n hours
    schedule.every(job_interval).hours.do(job)
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

def main():
    parser = argparse.ArgumentParser(description='Scheduled Google Flights Scraper')
    parser.add_argument('--routes', required=True, help='Path to routes JSON file')
    parser.add_argument('--interval', type=int, default=24, help='Job interval in hours')
    parser.add_argument('--months-ahead', type=int, default=3, help='Number of months ahead to search')
    parser.add_argument('--min-duration', type=int, default=6, help='Minimum flight duration in hours')
    parser.add_argument('--min-stay', type=int, default=7, help='Minimum stay duration in days')
    parser.add_argument('--max-stay', type=int, default=14, help='Maximum stay duration in days')
    parser.add_argument('--sort-by', default='price_per_hour', choices=['price', 'price_per_hour', 'duration_hours', 'value_score'],
                        help='Sort results by this field')
    parser.add_argument('--limit', type=int, default=20, help='Limit number of results')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--use-proxy', action='store_true', help='Use proxy settings from .env file')
    parser.add_argument('--disable-images', action='store_true', help='Disable images for faster loading')
    parser.add_argument('--screenshots', action='store_true', help='Take screenshots of search results')
    
    args = parser.parse_args()
    
    run_scheduled_scraper(
        routes_file=args.routes,
        job_interval=args.interval,
        months_ahead=args.months_ahead,
        min_duration=args.min_duration,
        min_stay=args.min_stay,
        max_stay=args.max_stay,
        sort_by=args.sort_by,
        limit=args.limit,
        headless=args.headless,
        use_proxy=args.use_proxy,
        disable_images=args.disable_images,
        take_screenshots=args.screenshots
    )

if __name__ == "__main__":
    main() 