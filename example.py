#!/usr/bin/env python3
"""
Google Flights Scraper Example Script

This example script demonstrates how to use the GoogleFlightsScraper class directly
to search for flights and find the best deals.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

from scrapers.flights_scraper import GoogleFlightsScraper
from utils.date_utils import get_next_n_months_date_range

def main():
    # Set up search parameters
    origin = "JFK"
    destination = "LHR"
    
    # Get date range for next 2 months
    start_date, end_date = get_next_n_months_date_range(2)
    
    # Create a departure date 2 weeks from now
    departure = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    
    # Create a return date 3 weeks from now (1 week trip)
    return_date = (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d")
    
    print(f"Example flight search: {origin} to {destination}")
    print(f"Departure: {departure}")
    print(f"Return: {return_date}")
    
    # Initialize the scraper
    scraper = GoogleFlightsScraper(headless=True, min_duration_hours=6)
    
    try:
        # Search for flights
        print("\nSearching for flights...")
        results = scraper.search_flights(origin, destination, departure, return_date)
        
        if not results:
            print("No flights found matching your criteria.")
            return
        
        print(f"Found {len(results)} flights!")
        
        # Find the best deals
        best_deals = scraper.find_best_deals(results, sort_by="price_per_hour", limit=5)
        
        # Display the results in a nice table
        print("\nTop 5 Best Deals:")
        df = pd.DataFrame(best_deals)
        
        # Format the DataFrame for display
        if 'price' in df.columns:
            df['price'] = df['price'].apply(lambda x: f"${x:.2f}")
        
        if 'price_per_hour' in df.columns:
            df['price_per_hour'] = df['price_per_hour'].apply(lambda x: f"${x:.2f}")
        
        if 'duration_hours' in df.columns:
            df['duration_hours'] = df['duration_hours'].apply(lambda x: f"{x:.1f} hrs")
        
        if 'airlines' in df.columns:
            df['airlines'] = df['airlines'].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
        
        # Select columns to display
        display_cols = ['price', 'airlines', 'duration_hours', 'stops', 'price_per_hour']
        available_cols = [col for col in display_cols if col in df.columns]
        
        # Print the table
        from tabulate import tabulate
        print(tabulate(df[available_cols], headers='keys', tablefmt='pretty', showindex=False))
        
        # Create a simple visualization of prices
        if len(results) > 1 and 'price' in df.columns and 'airlines' in df.columns:
            print("\nCreating price visualization...")
            
            # Convert price back to float for plotting
            plot_df = pd.DataFrame(results)
            
            # Simplify airlines for plotting
            plot_df['airline'] = plot_df['airlines'].apply(
                lambda x: x[0] if isinstance(x, list) and len(x) > 0 else 'Unknown'
            )
            
            # Set up the plot
            plt.figure(figsize=(10, 6))
            sns.set_style("whitegrid")
            
            # Create a boxplot of prices by airline
            ax = sns.boxplot(x='airline', y='price', data=plot_df)
            ax.set_title(f'Flight Prices: {origin} to {destination}')
            ax.set_xlabel('Airline')
            ax.set_ylabel('Price ($)')
            
            # Rotate x-axis labels for readability
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Save the plot
            plt.savefig('flight_prices.png')
            print("Visualization saved as 'flight_prices.png'")
            
    finally:
        # Always close the browser
        scraper.close()
        print("\nExample complete!")

if __name__ == "__main__":
    main() 