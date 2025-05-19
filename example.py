#!/usr/bin/env python3
"""
Example script demonstrating how to use the Google Flights Scraper programmatically.
"""

from scrapers.flights_scraper import GoogleFlightsScraper
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import os

def find_best_flight_deals():
    """Example function to find the best flight deals."""
    
    # Initialize the scraper
    scraper = GoogleFlightsScraper(
        headless=True,  # Run in headless mode
        min_duration_hours=6,  # Minimum flight duration
        disable_images=True  # Disable images for faster loading
    )
    
    try:
        # Define search parameters
        origin = "JFK"
        destination = "LHR"
        
        # Calculate dates for next week
        today = datetime.now()
        departure_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        return_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")
        
        print(f"Searching for flights from {origin} to {destination}")
        print(f"Departure: {departure_date}, Return: {return_date}")
        
        # Search for flights
        flights = scraper.search_flights(origin, destination, departure_date, return_date)
        
        # Find the best deals
        best_deals = scraper.find_best_deals(flights, sort_by="price_per_hour", limit=5)
        
        # Display results
        if best_deals:
            print(f"\nFound {len(best_deals)} best deals:")
            
            # Convert to DataFrame for easier display
            df = pd.DataFrame(best_deals)
            
            # Format airlines for display
            if 'airlines' in df.columns:
                df['airlines'] = df['airlines'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
            
            # Select columns to display
            display_cols = ['price', 'airlines', 'duration_hours', 'stops', 'price_per_hour']
            available_cols = [col for col in display_cols if col in df.columns]
            
            # Display the results
            print(df[available_cols].to_string(index=False))
            
            # Export results
            csv_path = scraper.export_to_csv(best_deals, "example_results.csv")
            json_path = scraper.export_to_json(best_deals, "example_results.json")
            
            print(f"\nResults exported to:")
            print(f"- CSV: {csv_path}")
            print(f"- JSON: {json_path}")
            
            # Take a screenshot
            screenshot_path = scraper.take_screenshot("example_screenshot.png")
            print(f"- Screenshot: {screenshot_path}")
            
            # Create a simple price visualization
            create_price_visualization(best_deals, f"{origin}_to_{destination}")
            
            return best_deals
        else:
            print("No flights found matching the criteria.")
            return []
        
    finally:
        # Always close the browser
        scraper.close()

def create_price_visualization(flights, title):
    """Create a simple price visualization chart."""
    if not flights:
        return
    
    # Create visualizations directory if it doesn't exist
    vis_dir = 'visualizations'
    os.makedirs(vis_dir, exist_ok=True)
    
    # Extract data for plotting
    df = pd.DataFrame(flights)
    
    # Format airlines for display
    if 'airlines' in df.columns:
        df['airlines'] = df['airlines'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
    
    # Create a simple bar chart of prices
    plt.figure(figsize=(10, 6))
    
    # Plot bars
    bars = plt.bar(df['airlines'], df['price'], color='skyblue')
    
    # Add price labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'${height:.2f}', ha='center', va='bottom')
    
    # Add details
    plt.title(f'Flight Prices for {title}')
    plt.xlabel('Airlines')
    plt.ylabel('Price ($)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save the figure
    output_path = os.path.join(vis_dir, f"{title}_prices.png")
    plt.savefig(output_path)
    print(f"- Price visualization: {output_path}")
    
    # Close the figure to free memory
    plt.close()

if __name__ == "__main__":
    find_best_flight_deals() 