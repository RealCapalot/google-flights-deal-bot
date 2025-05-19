#!/usr/bin/env python3
import argparse
import sys
import json
import os
from datetime import datetime, timedelta
from scrapers.flights_scraper import GoogleFlightsScraper
from scrapers.email_sender import EmailSender

def format_date(date_str):
    """Format date to YYYY-MM-DD if not already in that format"""
    if date_str is None:
        return None
        
    # Check if already in correct format
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        pass
    
    # Try other common formats
    for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y"]:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # If we get here, no format worked
    raise ValueError(f"Unrecognized date format: {date_str}. Please use YYYY-MM-DD format.")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Google Flights Scraper - Find the best flight deals")
    
    # Required arguments
    parser.add_argument("origin", help="Origin airport code (e.g., JFK)")
    parser.add_argument("destination", help="Destination airport code (e.g., LAX)")
    
    # Optional arguments with defaults
    parser.add_argument("-d", "--departure", required=True, help="Departure date (YYYY-MM-DD)")
    parser.add_argument("-r", "--return", dest="return_date", help="Return date (YYYY-MM-DD)")
    parser.add_argument("-s", "--sort", choices=["price", "duration_hours", "price_per_hour", "value_score"], 
                       default="price_per_hour", help="Sort results by this field")
    parser.add_argument("-l", "--limit", type=int, default=10, help="Maximum number of results to return")
    parser.add_argument("-m", "--min-duration", type=float, default=6.0, 
                       help="Minimum flight duration in hours (for long-haul flights)")
    
    # Export options
    parser.add_argument("--csv", action="store_true", help="Export results to CSV")
    parser.add_argument("--json", action="store_true", help="Export results to JSON")
    parser.add_argument("--screenshot", action="store_true", help="Take screenshot of search results")
    
    # Multiple dates
    parser.add_argument("--multi-date", type=int, help="Search for multiple dates (specify number of days)")
    parser.add_argument("--days-between", type=int, default=7, 
                       help="For return trips with multi-date, days between departure and return")
    
    # Browser options
    parser.add_argument("--no-headless", action="store_true", help="Don't run browser in headless mode")
    parser.add_argument("--show-images", action="store_true", help="Show images in browser")
    parser.add_argument("--proxy", help="Proxy URL (format: http://user:pass@host:port)")
    
    # Email notification options
    parser.add_argument("--email", help="Send results to this email address")
    parser.add_argument("--email-sender", help="Sender email address (if not provided, uses EMAIL_USER env variable)")
    parser.add_argument("--email-password", help="Sender email password (if not provided, uses EMAIL_PASSWORD env variable)")
    parser.add_argument("--email-server", default="smtp.gmail.com", help="SMTP server (default: smtp.gmail.com)")
    parser.add_argument("--email-port", type=int, default=587, help="SMTP port (default: 587)")
    
    args = parser.parse_args()
    
    # Format dates
    args.departure = format_date(args.departure)
    if args.return_date:
        args.return_date = format_date(args.return_date)
    
    return args

def display_results(flights, sort_by):
    """Display flight results in a readable format"""
    if not flights:
        print("No flights found matching your criteria.")
        return
    
    print(f"\n{'='*80}")
    print(f"Found {len(flights)} flights, sorted by {sort_by}:")
    print(f"{'='*80}")
    
    for i, flight in enumerate(flights, 1):
        airlines = ", ".join(flight["airlines"]) if isinstance(flight["airlines"], list) else flight["airlines"]
        duration = f"{flight['duration_hours']:.1f} hours"
        price = f"${flight['price']:.2f}"
        price_per_hour = f"${flight['price_per_hour']:.2f}/hr" if flight.get('price_per_hour') else "N/A"
        
        print(f"\n{i}. {airlines} - {price} ({price_per_hour})")
        print(f"   {flight['departure_airport']} ({flight['departure_time']}) → "
              f"{flight['arrival_airport']} ({flight['arrival_time']})")
        print(f"   Duration: {duration}, Stops: {flight['stops']}")
    
    print(f"\n{'='*80}")

def setup_email_sender(args):
    """Set up the email sender if email notifications are enabled"""
    if not args.email:
        return None
        
    # Check for credentials
    if not args.email_sender and not os.environ.get("EMAIL_USER"):
        print("Warning: No sender email provided. Please set EMAIL_USER environment variable or use --email-sender.")
    
    if not args.email_password and not os.environ.get("EMAIL_PASSWORD"):
        print("Warning: No sender password provided. Please set EMAIL_PASSWORD environment variable or use --email-password.")
    
    # Initialize email sender
    email_sender = EmailSender(
        sender_email=args.email_sender,
        sender_password=args.email_password,
        smtp_server=args.email_server,
        smtp_port=args.email_port
    )
    
    return email_sender

def main():
    """Main function to run the scraper"""
    args = parse_args()
    
    print(f"🛫 Google Flights Scraper")
    print(f"Searching flights from {args.origin} to {args.destination}")
    print(f"Departure: {args.departure}" + (f", Return: {args.return_date}" if args.return_date else ""))
    
    # Setup email sender if needed
    email_sender = setup_email_sender(args)
    if args.email:
        print(f"Email notifications will be sent to: {args.email}")
    
    try:
        # Initialize the scraper
        scraper = GoogleFlightsScraper(
            headless=not args.no_headless,
            min_duration_hours=args.min_duration,
            proxy_url=args.proxy,
            disable_images=not args.show_images
        )
        
        # Search for flights - single date or multi-date
        if args.multi_date:
            print(f"Searching across {args.multi_date} days starting from {args.departure}")
            results = scraper.get_multiple_date_options(
                args.origin, 
                args.destination, 
                args.departure,
                num_days=args.multi_date,
                return_trip=bool(args.return_date),
                days_between=args.days_between
            )
            
            # Process and display multi-date results
            all_flights = []
            
            for date, flights in results.items():
                print(f"\n📅 Date: {date}")
                best_flights = scraper.find_best_deals(flights, args.sort, args.limit)
                display_results(best_flights, args.sort)
                
                # Export if requested
                csv_path = None
                if args.csv:
                    filename = f"flights_{args.origin}_{args.destination}_{date}.csv"
                    csv_path = scraper.export_to_csv(best_flights, filename)
                    print(f"📄 CSV exported to {csv_path}")
                
                if args.json:
                    filename = f"flights_{args.origin}_{args.destination}_{date}.json"
                    json_path = scraper.export_to_json(best_flights, filename)
                    print(f"📄 JSON exported to {json_path}")
                
                # Store flights for each date
                for flight in best_flights:
                    flight["departure_date"] = date  # Add date information
                    all_flights.append(flight)
            
            # Take screenshot of the last search if requested
            screenshot_path = None
            if args.screenshot:
                screenshot_path = scraper.take_screenshot(f"flights_{args.origin}_{args.destination}.png")
                print(f"📸 Screenshot saved to {screenshot_path}")
            
            # Send email if requested with consolidated results
            if email_sender and args.email and all_flights:
                # Sort all flights again to find the best overall
                all_best_flights = scraper.find_best_deals(all_flights, args.sort, args.limit)
                
                # Send email
                email_sent = email_sender.send_flight_deals(
                    recipient_email=args.email,
                    flights=all_best_flights,
                    origin=args.origin,
                    destination=args.destination,
                    departure_date=args.departure,
                    return_date=args.return_date,
                    sort_by=args.sort,
                    screenshot_path=screenshot_path,
                    csv_path=csv_path if args.csv else None
                )
                
                if email_sent:
                    print(f"✉️ Flight deals sent to {args.email}")
                else:
                    print(f"❌ Failed to send email to {args.email}")
                
        else:
            # Single date search
            flights = scraper.search_best_deals(
                args.origin, 
                args.destination, 
                args.departure, 
                args.return_date,
                args.sort,
                args.limit
            )
            
            # Display results
            display_results(flights, args.sort)
            
            # Export if requested
            csv_path = None
            if args.csv:
                csv_path = scraper.export_to_csv(flights)
                print(f"📄 CSV exported to {csv_path}")
            
            json_path = None
            if args.json:
                json_path = scraper.export_to_json(flights)
                print(f"📄 JSON exported to {json_path}")
            
            screenshot_path = None
            if args.screenshot:
                screenshot_path = scraper.take_screenshot()
                print(f"📸 Screenshot saved to {screenshot_path}")
            
            # Send email if requested
            if email_sender and args.email and flights:
                email_sent = email_sender.send_flight_deals(
                    recipient_email=args.email,
                    flights=flights,
                    origin=args.origin,
                    destination=args.destination,
                    departure_date=args.departure,
                    return_date=args.return_date,
                    sort_by=args.sort,
                    screenshot_path=screenshot_path,
                    csv_path=csv_path
                )
                
                if email_sent:
                    print(f"✉️ Flight deals sent to {args.email}")
                else:
                    print(f"❌ Failed to send email to {args.email}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    finally:
        if 'scraper' in locals():
            scraper.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 