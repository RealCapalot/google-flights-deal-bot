#!/bin/bash
# Run the scheduled flight deals checker

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

# Run the scheduler with the routes file
echo "Starting scheduled flight deals checker..."
echo "Deals will be sent to: $EMAIL"
echo "Press Ctrl+C to stop the scheduler"

python schedule_deals.py --email "$EMAIL" --routes-file routes.json --interval 12 --round-trip 