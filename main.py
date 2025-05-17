import os
import json
import time
import argparse
import pandas as pd
from datetime import datetime
from tqdm import tqdm

from scrapers.flights_scraper import GoogleFlightsScraper
from utils.date_utils import generate_date_pairs, get_next_n_months_date_range
from utils.config import get_proxy_url

def save_results(results, filename):
    """Save results to JSON and CSV files"""
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Save as JSON
    json_path = os.path.join('data', f"{filename}.json")
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save as CSV
    if results:
        csv_path = os.path.join('data', f"{filename}.csv")
        df = pd.DataFrame(results)
        df.to_csv(csv_path, index=False)
    
    return json_path, csv_path if results else None

def main():
    parser = argparse.ArgumentParser(description='Google Flights Scraper for Long Flights')
    parser.add_argument('--origin', required=True, help='Origin airport code (e.g., SFO)')
    parser.add_argument('--destination', required=True, help='Destination airport code (e.g., NRT)')
    parser.add_argument('--start-date', help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', help='End date in YYYY-MM-DD format')
    parser.add_argument('--months-ahead', type=int, default=3, help='Number of months ahead to search')
    parser.add_argument('--min-duration', type=int, default=6, help='Minimum flight duration in hours to be considered a long flight')
    parser.add_argument('--min-stay', type=int, default=7, help='Minimum stay duration in days')
    parser.add_argument('--max-stay', type=int, default=14, help='Maximum stay duration in days')
    parser.add_argument('--sort-by', default='price_per_hour', choices=['price', 'price_per_hour', 'duration_hours', 'value_score'],
                        help='Sort results by this field')
    parser.add_argument('--limit', type=int, default=20, help='Limit number of results')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--one-way', action='store_true', help='Search for one-way flights only')
    parser.add_argument('--use-proxy', action='store_true', help='Use proxy settings from .env file')
    parser.add_argument('--disable-images', action='store_true', help='Disable images for faster loading')
    parser.add_argument('--screenshot', action='store_true', help='Take screenshot of each search results page')
    
    args = parser.parse_args()
    
    # Set up date range
    if args.start_date and args.end_date:
        start_date = args.start_date
        end_date = args.end_date
    else:
        start_date, end_date = get_next_n_months_date_range(args.months_ahead)
    
    # Get proxy URL if enabled
    proxy_url = get_proxy_url() if args.use_proxy else None
    
    # Initialize scraper
    scraper = GoogleFlightsScraper(
        headless=args.headless, 
        min_duration_hours=args.min_duration,
        proxy_url=proxy_url,
        disable_images=args.disable_images
    )
    
    try:
        all_results = []
        
        if args.one_way:
            # For one-way flights, we'll search each date individually
            print(f"Searching for one-way flights from {args.origin} to {args.destination} between {start_date} and {end_date}")
            
            # Generate all dates in range
            from datetime import datetime, timedelta
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            delta = (end - start).days + 1
            
            dates = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta)]
            
            for departure_date in tqdm(dates, desc="Searching dates"):
                results = scraper.search_flights(
                    args.origin, 
                    args.destination, 
                    departure_date
                )
                
                if args.screenshot:
                    screenshot_name = f"{args.origin}_to_{args.destination}_{departure_date}.png"
                    scraper.take_screenshot(screenshot_name)
                
                if results:
                    best_deals = scraper.find_best_deals(results, args.sort_by, args.limit)
                    
                    # Add date information to results
                    for deal in best_deals:
                        deal['departure_date'] = departure_date
                        deal['return_date'] = None
                        all_results.extend(best_deals)
                
                # Wait between requests to avoid rate limiting
                time.sleep(2)
                
        else:
            # For round-trip flights, generate all date pairs
            date_pairs = generate_date_pairs(
                start_date, 
                end_date, 
                trip_min_days=args.min_stay, 
                trip_max_days=args.max_stay
            )
            
            print(f"Searching for round-trip flights from {args.origin} to {args.destination}")
            print(f"Generated {len(date_pairs)} date pairs to search")
            
            for departure_date, return_date in tqdm(date_pairs, desc="Searching date pairs"):
                results = scraper.search_flights(
                    args.origin, 
                    args.destination, 
                    departure_date,
                    return_date
                )
                
                if args.screenshot:
                    screenshot_name = f"{args.origin}_to_{args.destination}_{departure_date}_to_{return_date}.png"
                    scraper.take_screenshot(screenshot_name)
                
                if results:
                    best_deals = scraper.find_best_deals(results, args.sort_by, args.limit)
                    
                    # Add date information to results
                    for deal in best_deals:
                        deal['departure_date'] = departure_date
                        deal['return_date'] = return_date
                        all_results.extend(best_deals)
                
                # Wait between requests to avoid rate limiting
                time.sleep(2)
        
        # Sort all results again to find the overall best deals
        final_results = scraper.find_best_deals(all_results, args.sort_by, args.limit)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{args.origin}_to_{args.destination}_{timestamp}"
        json_path, csv_path = save_results(final_results, filename)
        
        print(f"\nSearch complete! Found {len(final_results)} deals.")
        print(f"Results saved to:")
        print(f"- JSON: {json_path}")
        if csv_path:
            print(f"- CSV: {csv_path}")
        
        # Print top 5 results
        if final_results:
            print("\nTop 5 results:")
            df = pd.DataFrame(final_results[:5])
            
            # Select specific columns to display
            display_cols = ['price', 'airlines', 'duration_hours', 'stops', 
                           'departure_date', 'return_date', 'price_per_hour']
            
            available_cols = [col for col in display_cols if col in df.columns]
            print(df[available_cols].to_string(index=False))
            
    finally:
        # Always close the browser
        scraper.close()

if __name__ == "__main__":
    main() 