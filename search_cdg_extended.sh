#!/bin/bash
# Run an extended search for CDG routes up to 500 days in advance

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

echo "=========================================="
echo "Extended Flight Search - CDG Routes"
echo "=========================================="
echo "This script will search for flights from CDG"
echo "over a 500-day period with a minimum 3-day stay"
echo "Results will be sent to: $EMAIL"
echo "This search will take a long time to complete."
echo "It will run in batches to avoid rate limiting."
echo "=========================================="
echo ""
echo "Press Enter to start or Ctrl+C to cancel..."
read

echo "Starting extended search..."
python extended_search.py --cdg-only --export \
    --min-stay 3 --max-stay 21 --stay-interval 3 \
    --batch-size 10 --batch-pause 120 \
    --email "$EMAIL" 