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

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from run_bot import run_bot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('bot_scheduler')

def job():
    """Run the bot with error handling"""
    try:
        logger.info("Starting scheduled flight search...")
        run_bot()
        logger.info("Flight search completed successfully")
    except Exception as e:
        logger.error(f"Error running flight search: {str(e)}")
        # Wait 5 minutes before retrying
        time.sleep(300)
        try:
            logger.info("Retrying flight search...")
            run_bot()
            logger.info("Flight search completed successfully on retry")
        except Exception as e:
            logger.error(f"Error on retry: {str(e)}")

def main():
    """Main function to run the scheduler"""
    # Run immediately on startup
    job()
    
    # Schedule to run every 6 hours
    schedule.every(6).hours.do(job)
    
    logger.info("Bot scheduler started. Running every 6 hours.")
    
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