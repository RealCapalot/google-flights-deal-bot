#!/usr/bin/env python3
"""
Scheduled runner for Google Flights Deal Bot
Runs the bot on a schedule and handles errors
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
import schedule
from scrapers.flights_scraper import GoogleFlightsScraper
from scrapers.email_sender import EmailSender
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_search():
    try:
        logger.info("Starting flight search...")
        
        # Initialize scraper with premium only mode
        scraper = GoogleFlightsScraper(
            headless=True,
            min_duration_hours=6,
            premium_only=True,
            disable_images=True
        )
        
        # Initialize email sender
        email_sender = EmailSender(
            sender_email=os.getenv('EMAIL_SENDER', 'aleczooyork@gmail.com'),
            sender_password=os.getenv('EMAIL_PASSWORD'),
            recipient_email=os.getenv('EMAIL_RECIPIENT', 'alec.dc29@gmail.com')
        )
        
        # Get current date and dates for next 100 days
        start_date = datetime.now().strftime("%Y-%m-%d")
        
        # Major routes to search
        routes = [
            ("CDG", "JFK"),  # Paris to New York
            ("CDG", "LAX"),  # Paris to Los Angeles
            ("CDG", "SIN"),  # Paris to Singapore
            ("CDG", "DXB"),  # Paris to Dubai
            ("CDG", "BKK"),  # Paris to Bangkok
            ("MAD", "JFK"),  # Madrid to New York
            ("LIS", "JFK"),  # Lisbon to New York
            ("LHR", "JFK"),  # London to New York
            ("DXB", "JFK"),  # Dubai to New York
            ("AMS", "JFK"),  # Amsterdam to New York
            ("MXP", "JFK"),  # Milan to New York
            ("FCO", "JFK"),  # Rome to New York
        ]
        
        all_deals = []
        
        # Search each route
        for origin, destination in routes:
            logger.info(f"Searching route: {origin} to {destination}")
            
            # Search 100 dates in parallel
            results = scraper.get_multiple_date_options(
                origin=origin,
                destination=destination,
                start_date=start_date,
                num_days=100,
                return_trip=False,
                max_workers=10  # Adjust based on your system's capabilities
            )
            
            # Process results
            for date, flights in results.items():
                if flights:
                    # Find best deals for this date
                    best_deals = scraper.find_best_deals(
                        flights,
                        sort_by="discount_percentage",
                        limit=5,
                        discount_threshold=35
                    )
                    
                    if best_deals:
                        for deal in best_deals:
                            deal['route'] = f"{origin}-{destination}"
                            deal['date'] = date
                            all_deals.append(deal)
        
        # If we found any deals, send email
        if all_deals:
            # Sort all deals by discount percentage
            all_deals.sort(key=lambda x: x.get('discount_percentage', 0), reverse=True)
            
            # Take screenshot of the best deals
            screenshot_path = scraper.take_screenshot()
            
            # Export deals to CSV
            csv_path = scraper.export_to_csv(all_deals)
            
            # Send email with results
            email_sender.send_deals_email(all_deals, screenshot_path, csv_path)
            logger.info(f"Found {len(all_deals)} deals and sent email")
        else:
            logger.info("No deals found")
        
    except Exception as e:
        logger.error(f"Error in run_search: {str(e)}")
    finally:
        scraper.close()

def main():
    """Main function to run the scheduler"""
    # Run immediately on startup
    run_search()
    
    # Schedule to run every 4 hours
    schedule.every(4).hours.do(run_search)
    
    logger.info("Bot scheduler started. Running every 4 hours.")
    
    # Keep the script running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            time.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    main() 