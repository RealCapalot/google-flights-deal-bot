#!/bin/bash
# Run the Google Flights Scraper

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

# Run the scraper with arguments passed to this script
python main.py "$@" 