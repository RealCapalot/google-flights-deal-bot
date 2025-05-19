#!/usr/bin/env python3
"""
Google Flights Deal Bot - Automated flight deal finder
Runs extended search with email notifications for premium cabin deals
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extended_search import run_extended_search
from scrapers.email_sender import EmailSender
from scrapers.flights_scraper import GoogleFlightsScraper

# Email configuration from environment variables
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT', 'alec.dc29@gmail.com')
EMAIL_SENDER = os.getenv('EMAIL_SENDER', 'aleczooyork@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'vjgd inkg gjle ksmv')

def run_bot():
    """Run the flight deal bot with email notifications"""
    # Initialize email sender
    email_sender = EmailSender(
        sender_email=EMAIL_SENDER,
        sender_password=EMAIL_PASSWORD,
        recipient_email=EMAIL_RECIPIENT
    )
    
    # Initialize scraper
    scraper = GoogleFlightsScraper(
        headless=True,
        min_duration_hours=6,
        premium_only=True  # Only search for Business and First class
    )
    
    try:
        # Load routes from file
        with open('routes.json', 'r') as f:
            routes = json.load(f)
        
        # Get current date and calculate end date (500 days from now)
        start_date = datetime.now()
        end_date = start_date + timedelta(days=500)
        
        # Search parameters
        search_params = {
            'routes_file': 'routes.json',
            'cdg_only': True,
            'email': True,
            'max_days': 500,  # Search up to 500 days ahead
            'min_stay': 3,    # Minimum stay duration
            'max_stay': 30,   # Maximum stay duration
            'min_duration': 6, # Minimum flight duration in hours
            'premium_only': True,  # Only business and first class
            'discount_threshold': 35  # Minimum discount percentage
        }
        
        # Run extended search
        run_extended_search(scraper, email_sender, search_params)
        
    except Exception as e:
        print(f"Error running bot: {str(e)}")
    finally:
        scraper.close()

if __name__ == "__main__":
    run_bot() 