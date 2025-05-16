from datetime import datetime, timedelta

def generate_date_pairs(start_date, end_date, trip_min_days=7, trip_max_days=14, date_format="%Y-%m-%d"):
    """
    Generate departure and return date pairs for a given date range.
    
    Args:
        start_date (str): Start date in format YYYY-MM-DD
        end_date (str): End date in format YYYY-MM-DD
        trip_min_days (int): Minimum trip duration in days
        trip_max_days (int): Maximum trip duration in days
        date_format (str): Date string format
        
    Returns:
        list: List of (departure_date, return_date) tuples
    """
    start = datetime.strptime(start_date, date_format)
    end = datetime.strptime(end_date, date_format)
    
    date_pairs = []
    
    current_date = start
    while current_date <= end:
        # For each potential departure date
        for trip_duration in range(trip_min_days, trip_max_days + 1):
            return_date = current_date + timedelta(days=trip_duration)
            
            # Make sure return date is within our search range
            if return_date <= end:
                date_pairs.append((
                    current_date.strftime(date_format),
                    return_date.strftime(date_format)
                ))
        
        # Move to next potential departure date
        current_date += timedelta(days=1)
    
    return date_pairs

def generate_date_range(start_date, num_days, date_format="%Y-%m-%d"):
    """
    Generate a list of dates starting from start_date.
    
    Args:
        start_date (str): Start date in format YYYY-MM-DD
        num_days (int): Number of days to generate
        date_format (str): Date string format
        
    Returns:
        list: List of date strings
    """
    start = datetime.strptime(start_date, date_format)
    
    dates = []
    for i in range(num_days):
        date = start + timedelta(days=i)
        dates.append(date.strftime(date_format))
    
    return dates

def get_next_n_months_date_range(n=3, date_format="%Y-%m-%d"):
    """
    Get date range for the next n months.
    
    Args:
        n (int): Number of months ahead
        date_format (str): Date string format
        
    Returns:
        tuple: (start_date, end_date) strings
    """
    today = datetime.now()
    start_date = today.strftime(date_format)
    
    # Add n months (approximate)
    end_date = today + timedelta(days=30 * n)
    end_date_str = end_date.strftime(date_format)
    
    return start_date, end_date_str 