"""
Visualization utilities for flight data analysis.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def create_price_by_airline_chart(flights_data, origin, destination, save_path=None):
    """
    Create a boxplot of prices by airline.
    
    Args:
        flights_data (list): List of flight dictionaries
        origin (str): Origin airport code
        destination (str): Destination airport code
        save_path (str, optional): Path to save the chart. If None, chart will be displayed.
    
    Returns:
        str: Path to the saved chart file, or None if not saved
    """
    if not flights_data:
        print("No flight data available for visualization")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(flights_data)
    
    # Extract primary airline for each flight
    df['airline'] = df['airlines'].apply(
        lambda x: x[0] if isinstance(x, list) and len(x) > 0 else 'Unknown'
    )
    
    # Set up the plot
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    
    # Create a boxplot of prices by airline
    ax = sns.boxplot(x='airline', y='price', data=df)
    ax.set_title(f'Flight Prices: {origin} to {destination}')
    ax.set_xlabel('Airline')
    ax.set_ylabel('Price ($)')
    
    # Rotate x-axis labels for readability
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save or display the chart
    if save_path:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        plt.savefig(save_path)
        plt.close()
        return save_path
    else:
        plt.show()
        return None

def create_price_by_date_chart(flights_data, origin, destination, save_path=None):
    """
    Create a scatter plot of prices by departure date.
    
    Args:
        flights_data (list): List of flight dictionaries with departure_date key
        origin (str): Origin airport code
        destination (str): Destination airport code
        save_path (str, optional): Path to save the chart. If None, chart will be displayed.
    
    Returns:
        str: Path to the saved chart file, or None if not saved
    """
    if not flights_data or 'departure_date' not in flights_data[0]:
        print("No date information available for visualization")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(flights_data)
    
    # Convert departure_date to datetime
    df['departure_date'] = pd.to_datetime(df['departure_date'])
    
    # Set up the plot
    plt.figure(figsize=(12, 6))
    sns.set_style("whitegrid")
    
    # Create a scatter plot of prices by date
    ax = sns.scatterplot(
        x='departure_date', 
        y='price', 
        hue='stops' if 'stops' in df.columns else None,
        size='duration_hours' if 'duration_hours' in df.columns else None,
        sizes=(20, 200),
        alpha=0.7,
        data=df
    )
    
    ax.set_title(f'Flight Prices by Date: {origin} to {destination}')
    ax.set_xlabel('Departure Date')
    ax.set_ylabel('Price ($)')
    
    # Format x-axis as dates
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    
    # Save or display the chart
    if save_path:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        plt.savefig(save_path)
        plt.close()
        return save_path
    else:
        plt.show()
        return None

def create_price_per_hour_chart(flights_data, origin, destination, save_path=None):
    """
    Create a scatter plot of price vs duration with price per hour as color.
    
    Args:
        flights_data (list): List of flight dictionaries
        origin (str): Origin airport code
        destination (str): Destination airport code
        save_path (str, optional): Path to save the chart. If None, chart will be displayed.
    
    Returns:
        str: Path to the saved chart file, or None if not saved
    """
    if not flights_data:
        print("No flight data available for visualization")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(flights_data)
    
    if 'price_per_hour' not in df.columns or 'duration_hours' not in df.columns:
        print("Missing price_per_hour or duration_hours in data")
        return None
    
    # Set up the plot
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    
    # Create a scatter plot of price vs duration with price/hour as color
    scatter = plt.scatter(
        df['duration_hours'],
        df['price'],
        c=df['price_per_hour'],
        cmap='viridis_r',  # Reversed viridis (lower values = better = green)
        alpha=0.7,
        s=100
    )
    
    plt.colorbar(scatter, label='Price per Hour ($)')
    plt.title(f'Flight Value Analysis: {origin} to {destination}')
    plt.xlabel('Flight Duration (hours)')
    plt.ylabel('Price ($)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save or display the chart
    if save_path:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        plt.savefig(save_path)
        plt.close()
        return save_path
    else:
        plt.show()
        return None

def create_dashboard(flights_data, origin, destination, output_dir='visualizations'):
    """
    Create a complete dashboard of flight visualizations.
    
    Args:
        flights_data (list): List of flight dictionaries
        origin (str): Origin airport code
        destination (str): Destination airport code
        output_dir (str): Directory to save visualizations
        
    Returns:
        list: Paths to all created visualization files
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate all visualizations
    charts = []
    
    # 1. Price by airline chart
    airline_chart = create_price_by_airline_chart(
        flights_data, 
        origin, 
        destination, 
        save_path=os.path.join(output_dir, f"{origin}_to_{destination}_prices_by_airline.png")
    )
    if airline_chart:
        charts.append(airline_chart)
    
    # 2. Price by date chart (if date information is available)
    if flights_data and 'departure_date' in flights_data[0]:
        date_chart = create_price_by_date_chart(
            flights_data, 
            origin, 
            destination, 
            save_path=os.path.join(output_dir, f"{origin}_to_{destination}_prices_by_date.png")
        )
        if date_chart:
            charts.append(date_chart)
    
    # 3. Price per hour value chart
    value_chart = create_price_per_hour_chart(
        flights_data, 
        origin, 
        destination, 
        save_path=os.path.join(output_dir, f"{origin}_to_{destination}_value_analysis.png")
    )
    if value_chart:
        charts.append(value_chart)
    
    return charts 