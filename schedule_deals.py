#!/usr/bin/env python3
"""
Scheduled Google Flights deal finder.
This script runs regular checks for flight deals and sends notifications via email.
"""

import os
import time
import json
import logging
import argparse
import schedule
from datetime import datetime, timedelta

from scrapers.flights_scraper import GoogleFlightsScraper
from scrapers.email_sender import EmailSender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("flight_deals.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("schedule_deals")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Scheduled Google Flights Deal Checker")
    
    # Route configuration
    parser.add_argument("--routes-file", help="JSON file containing routes to check")
    parser.add_argument("--origin", help="Origin airport code (e.g., JFK)")
    parser.add_argument("--destination", help="Destination airport code (e.g., LAX)")
    
    # Email settings
    parser.add_argument("--email", required=True, help="Email address to send notifications to")
    parser.add_argument("--email-sender", help="Sender email address")
    parser.add_argument("--email-password", help="Sender email password")
    
    # Schedule settings
    parser.add_argument("--interval", type=int, default=12, help="Check interval in hours (default: 12)")
    parser.add_argument("--start-days", type=int, default=7, help="Start checking from X days in the future (default: 7)")
    parser.add_argument("--num-days", type=int, default=60, help="Number of days to check (default: 60)")
    parser.add_argument("--check-days", type=int, default=5, help="Check every X days (default: 5)")
    
    # Search settings
    parser.add_argument("--min-stay", type=int, default=7, help="Minimum stay duration for round trips (default: 7)")
    parser.add_argument("--max-stay", type=int, default=14, help="Maximum stay duration for round trips (default: 14)")
    parser.add_argument("--min-duration", type=float, default=6.0, help="Minimum flight duration hours (default: 6.0)")
    parser.add_argument("--round-trip", action="store_true", help="Search for round-trip flights")
    
    args = parser.parse_args()
    
    # Validate args
    if not args.routes_file and not (args.origin and args.destination):
        parser.error("Either --routes-file or both --origin and --destination must be provided")
    
    return args

def load_routes(routes_file):
    """Load routes from a JSON file"""
    if not os.path.exists(routes_file):
        logger.error(f"Routes file not found: {routes_file}")
        return []
    
    try:
        with open(routes_file, 'r') as f:
            routes = json.load(f)
        
        logger.info(f"Loaded {len(routes)} routes from {routes_file}")
        return routes
    except Exception as e:
        logger.error(f"Error loading routes file: {str(e)}")
        return []

def generate_dates(start_days, num_days, check_days):
    """Generate a list of dates to check"""
    start_date = datetime.now() + timedelta(days=start_days)
    dates = []
    
    for i in range(0, num_days, check_days):
        date = start_date + timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))
    
    return dates

def generate_date_pairs(dates, min_stay, max_stay):
    """Generate departure and return date pairs for round trips"""
    date_pairs = []
    
    for dep_date in dates:
        dep_datetime = datetime.strptime(dep_date, "%Y-%m-%d")
        
        for stay_length in range(min_stay, max_stay + 1):
            ret_datetime = dep_datetime + timedelta(days=stay_length)
            ret_date = ret_datetime.strftime("%Y-%m-%d")
            date_pairs.append((dep_date, ret_date))
    
    return date_pairs

def check_flight_deals(args, email_sender):
    """Check for flight deals and send notifications"""
    logger.info("Starting flight deal check...")
    
    # Set up routes to check
    routes = []
    if args.routes_file:
        routes = load_routes(args.routes_file)
    else:
        routes = [{
            "origin": args.origin,
            "destination": args.destination,
            "description": f"{args.origin} to {args.destination}"
        }]
    
    if not routes:
        logger.error("No routes to check")
        return
    
    # Generate dates to check
    dates = generate_dates(args.start_days, args.num_days, args.check_days)
    logger.info(f"Generated {len(dates)} dates to check")
    
    # For round trips, generate date pairs
    date_pairs = []
    if args.round_trip:
        date_pairs = generate_date_pairs(dates, args.min_stay, args.max_stay)
        logger.info(f"Generated {len(date_pairs)} date pairs for round trips")
    
    # Initialize scraper
    scraper = GoogleFlightsScraper(
        headless=True,
        min_duration_hours=args.min_duration,
        disable_images=True
    )
    
    try:
        for route in routes:
            origin = route["origin"]
            destination = route["destination"]
            description = route.get("description", f"{origin} to {destination}")
            
            logger.info(f"Checking route: {description}")
            
            all_flights = []
            
            if args.round_trip:
                # Check round-trip flights
                for dep_date, ret_date in date_pairs:
                    try:
                        logger.info(f"Checking {origin} to {destination}: {dep_date} - {ret_date}")
                        flights = scraper.search_flights(origin, destination, dep_date, ret_date)
                        
                        if flights:
                            for flight in flights:
                                flight["departure_date"] = dep_date
                                flight["return_date"] = ret_date
                            all_flights.extend(flights)
                            logger.info(f"Found {len(flights)} flights for {dep_date} - {ret_date}")
                        
                        # Short pause between searches
                        time.sleep(2)
                    except Exception as e:
                        logger.error(f"Error checking {dep_date} - {ret_date}: {str(e)}")
            else:
                # Check one-way flights
                for dep_date in dates:
                    try:
                        logger.info(f"Checking {origin} to {destination}: {dep_date}")
                        flights = scraper.search_flights(origin, destination, dep_date)
                        
                        if flights:
                            for flight in flights:
                                flight["departure_date"] = dep_date
                            all_flights.extend(flights)
                            logger.info(f"Found {len(flights)} flights for {dep_date}")
                        
                        # Short pause between searches
                        time.sleep(2)
                    except Exception as e:
                        logger.error(f"Error checking {dep_date}: {str(e)}")
            
            # Process results for this route
            if all_flights:
                # Find the best deals
                best_deals = scraper.find_best_deals(all_flights, sort_by="price_per_hour", limit=10)
                
                # Take a screenshot of the last search
                screenshot_path = scraper.take_screenshot(f"{origin}_to_{destination}.png")
                
                # Export to CSV
                csv_path = scraper.export_to_csv(best_deals, f"{origin}_to_{destination}.csv")
                
                # Send email with the deals
                if email_sender and args.email:
                    # Determine departure and return dates to display in email
                    if args.round_trip:
                        # Use earliest departure date
                        earliest_dep = min(f["departure_date"] for f in best_deals)
                        # Use latest return date
                        latest_ret = max(f["return_date"] for f in best_deals)
                        email_sent = email_sender.send_flight_deals(
                            recipient_email=args.email,
                            flights=best_deals,
                            origin=origin,
                            destination=destination,
                            departure_date=earliest_dep,
                            return_date=latest_ret,
                            sort_by="price_per_hour",
                            screenshot_path=screenshot_path,
                            csv_path=csv_path
                        )
                    else:
                        # Use earliest departure date
                        earliest_dep = min(f["departure_date"] for f in best_deals)
                        email_sent = email_sender.send_flight_deals(
                            recipient_email=args.email,
                            flights=best_deals,
                            origin=origin,
                            destination=destination,
                            departure_date=earliest_dep,
                            sort_by="price_per_hour",
                            screenshot_path=screenshot_path,
                            csv_path=csv_path
                        )
                    
                    if email_sent:
                        logger.info(f"Flight deals for {description} sent to {args.email}")
                    else:
                        logger.error(f"Failed to send email for {description}")
                
                logger.info(f"Found {len(best_deals)} best deals for {description}")
            else:
                logger.info(f"No flights found for {description}")
    
    except Exception as e:
        logger.error(f"Error checking flight deals: {str(e)}")
    finally:
        scraper.close()
    
    logger.info("Flight deal check completed")

def schedule_job(args, email_sender):
    """Schedule the job to run at the specified interval"""
    # Run immediately first
    check_flight_deals(args, email_sender)
    
    # Schedule for regular runs
    interval_hours = args.interval
    logger.info(f"Scheduling job to run every {interval_hours} hours")
    
    schedule.every(interval_hours).hours.do(check_flight_deals, args=args, email_sender=email_sender)
    
    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Job scheduler stopped by user")

def main():
    """Main function"""
    args = parse_args()
    
    # Initialize email sender
    email_sender = EmailSender(
        sender_email=args.email_sender,
        sender_password=args.email_password
    )
    
    # Schedule and run the job
    schedule_job(args, email_sender)

if __name__ == "__main__":
    main() 