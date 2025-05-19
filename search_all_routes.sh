#!/bin/bash
# Run an extended search for all major European and Middle Eastern routes

EMAIL="alec.dc29@gmail.com"  # The user's email

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is required but could not be found"
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Check for email credentials
if [ -z "$EMAIL_USER" ]; then
    echo "Warning: EMAIL_USER environment variable not set"
    echo "Please set the environment variable or enter the sender email address:"
    read EMAIL_USER
    export EMAIL_USER
fi

if [ -z "$EMAIL_PASSWORD" ]; then
    echo "Warning: EMAIL_PASSWORD environment variable not set"
    echo "Please set the environment variable or enter the sender email password:"
    read -s EMAIL_PASSWORD  # -s flag hides the input
    export EMAIL_PASSWORD
    echo "" # New line after hidden input
fi

# Function to search specific cities
search_cities() {
    local cities=("$@")
    local search_params=""
    
    # Build filter string for the cities
    for city in "${cities[@]}"; do
        if [ -z "$search_params" ]; then
            search_params="--origin-filter $city"
        else
            search_params="$search_params,$city"
        fi
    done
    
    echo "Searching routes from: ${cities[*]}"
    python extended_search.py $search_params --export \
        --min-stay 3 --max-stay 21 --stay-interval 3 \
        --batch-size 10 --batch-pause 120 \
        --check-interval 14 --max-days 400 \
        --email "$EMAIL"
}

echo "=========================================="
echo "Extended Flight Search - All Major Routes"
echo "=========================================="
echo "This script will search for flights across 40+ major international routes"
echo "over a 400-day period with a minimum 3-day stay"
echo "Results will be sent to: $EMAIL"
echo "This search will take a very long time to complete."
echo ""
echo "Choose an option:"
echo "1. Search ALL routes (will take many hours)"
echo "2. Search only CDG routes"
echo "3. Search only Madrid (MAD) routes"
echo "4. Search only London (LHR) routes"
echo "5. Search only Dubai (DXB) routes"
echo "6. Search only Amsterdam (AMS) routes"
echo "7. Search only Italian routes (Rome FCO & Milan MXP)"
echo "8. Search only Lisbon (LIS) routes"
echo "9. Exit"
echo "=========================================="
read -p "Enter your choice (1-9): " choice

# Create a custom filter file for extended_search.py
cat > origin_filter.py << EOF
#!/usr/bin/env python3
"""Filter for search routes by origin"""

def filter_routes(routes, origins):
    """Filter routes by origin airport codes"""
    if not origins:
        return routes
        
    origins = origins.split(",")
    return [r for r in routes if r["origin"] in origins]
EOF

# Add filtering capability to extended_search.py
if ! grep -q "origin_filter" extended_search.py; then
    echo "Adding filtering capability to extended_search.py..."
    sed -i.bak '
    /import argparse/a\
import sys\
import os.path\
sys.path.append(os.path.dirname(os.path.abspath(__file__)))\
try:\
    from origin_filter import filter_routes\
except ImportError:\
    def filter_routes(routes, origins):\
        """Default filter if module not found"""\
        if not origins:\
            return routes\
        origins = origins.split(",")\
        return [r for r in routes if r["origin"] in origins]\
    ' extended_search.py
    
    sed -i.bak '
    /# Route configuration/a\
    parser.add_argument("--origin-filter", help="Filter by origin airports (comma-separated)")\
    ' extended_search.py
    
    sed -i.bak '
    /    # Filter for CDG routes only if requested/a\
        # Apply origin filter if specified\
        if args.origin_filter:\
            routes = filter_routes(routes, args.origin_filter)\
    ' extended_search.py
fi

case $choice in
    1)
        echo "Starting search for ALL routes..."
        python extended_search.py --export \
            --min-stay 3 --max-stay 21 --stay-interval 3 \
            --batch-size 10 --batch-pause 120 \
            --check-interval 14 --max-days 400 \
            --email "$EMAIL"
        ;;
    2)
        search_cities "CDG"
        ;;
    3)
        search_cities "MAD"
        ;;
    4)
        search_cities "LHR"
        ;;
    5)
        search_cities "DXB"
        ;;
    6)
        search_cities "AMS"
        ;;
    7)
        search_cities "FCO" "MXP"
        ;;
    8)
        search_cities "LIS"
        ;;
    9)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac 