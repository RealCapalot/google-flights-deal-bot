# Google Flights Deal Bot

An automated tool that searches for premium cabin flight deals (Business and First Class) from Google Flights. The bot monitors prices across multiple routes and sends email notifications when it finds significant discounts.

## Features

- Searches for Business and First Class flights
- Monitors prices up to 500 days in advance
- Configurable stay durations (3-30 days)
- Email notifications with:
  - Direct Google Flights links
  - Screenshots of search results
  - CSV files with detailed information
- Price tracking and discount analysis
- Automated scheduling (runs every 6 hours)

## Requirements

- Python 3.8+
- Chrome browser
- Gmail account for notifications

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/google-flights-deal-bot.git
cd google-flights-deal-bot
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your email settings in `run_bot.py`:
```python
EMAIL_RECIPIENT = "your-email@example.com"
EMAIL_SENDER = "your-gmail@gmail.com"
EMAIL_PASSWORD = "your-app-specific-password"
```

5. Configure your routes in `routes.json`:
```json
{
    "routes": [
        {
            "origin": "CDG",
            "destination": "JFK"
        }
    ]
}
```

## Usage

1. Start the bot:
```bash
./start_bot.sh
```

The bot will:
- Run immediately and check for deals
- Continue running every 6 hours
- Send email notifications when good deals are found
- Store price history for better deal detection

## Configuration

You can customize the bot's behavior by modifying these parameters in `run_bot.py`:

- `min_duration_hours`: Minimum flight duration (default: 6)
- `premium_only`: Only search for Business and First class (default: True)
- `discount_threshold`: Minimum discount percentage (default: 35%)
- `max_days`: Maximum days to search ahead (default: 500)
- `min_stay`: Minimum stay duration (default: 3 days)
- `max_stay`: Maximum stay duration (default: 30 days)

## Security Notes

- Never commit your email password or API keys
- Use environment variables or a secure configuration file
- Keep your `price_database.json` local and backed up

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 