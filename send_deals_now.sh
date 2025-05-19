#!/bin/bash
# Send flight deals to email immediately

EMAIL="alec.dc29@gmail.com"  # The user's email

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is required but could not be found"
    exit 1
fi

# Check if virtual environment exists, activate if it does
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Please run ./run.sh first to set up the environment."
    exit 1
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

# Parse arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <origin> <destination> <departure_date> [return_date]"
    echo "Example: $0 JFK LHR 2023-12-01 2023-12-15"
    exit 1
fi

ORIGIN="$1"
DESTINATION="$2"
DEPARTURE_DATE="$3"
RETURN_DATE="$4"

echo "Searching for flights from $ORIGIN to $DESTINATION"
echo "Departure: $DEPARTURE_DATE"
if [ -n "$RETURN_DATE" ]; then
    echo "Return: $RETURN_DATE"
    python main.py "$ORIGIN" "$DESTINATION" -d "$DEPARTURE_DATE" -r "$RETURN_DATE" --email "$EMAIL" --csv --json --screenshot
else
    python main.py "$ORIGIN" "$DESTINATION" -d "$DEPARTURE_DATE" --email "$EMAIL" --csv --json --screenshot
fi 