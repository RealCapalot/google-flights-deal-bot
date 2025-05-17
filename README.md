# Google Flights Scraper for Long Flight Deals

A Python-based tool to scrape Google Flights and find the best deals for long flights, with a focus on value (price per hour of flight time).

## Features

- Scrapes Google Flights search results using Selenium
- Focuses on long flights (configurable, default minimum 6 hours)
- Finds the best deals based on multiple criteria:
  - Lowest price
  - Best price per hour (default)
  - Longest duration
  - Value score (normalized price per hour)
- Supports one-way and round-trip searches
- Date range generation for flexible travel dates
- Scheduled scraping for continuous monitoring
- Save results in JSON and CSV formats
- Proxy support for avoiding rate limits
- Data visualization tools and dashboards
- Screenshot capabilities for search results

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd google_flights_scraper
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Make sure you have Chrome installed, as the scraper uses Chrome via Selenium.

4. (Optional) Copy the env.example file to .env and customize settings:
   ```
   cp env.example .env
   ```

## Usage

### Quick Search

To run a quick search for flights between two locations:

```bash
python main.py --origin SFO --destination NRT --headless
```

### Advanced Options

The scraper supports several command-line options:

```bash
python main.py --origin SFO --destination NRT \
  --start-date 2023-12-01 --end-date 2024-03-01 \
  --min-duration 8 --min-stay 10 --max-stay 21 \
  --sort-by price --limit 10 --headless --disable-images
```

### Example Script

The included example.py script demonstrates a simple use case:

```bash
python example.py
```

This will:
1. Search for flights from JFK to LHR
2. Show the top 5 best deals
3. Create a price visualization chart

### Command Line Arguments

- `--origin`: Origin airport code (e.g., SFO) - Required
- `--destination`: Destination airport code (e.g., NRT) - Required
- `--start-date`: Start date in YYYY-MM-DD format (defaults to today)
- `--end-date`: End date in YYYY-MM-DD format (defaults to 3 months from today)
- `--months-ahead`: Number of months ahead to search if start/end dates aren't provided (default: 3)
- `--min-duration`: Minimum flight duration in hours (default: 6)
- `--min-stay`: Minimum stay duration in days (default: 7)
- `--max-stay`: Maximum stay duration in days (default: 14)
- `--sort-by`: Sort results by this field - options: price, price_per_hour, duration_hours, value_score (default: price_per_hour)
- `--limit`: Limit number of results (default: 20)
- `--headless`: Run browser in headless mode (more efficient)
- `--one-way`: Search for one-way flights only
- `--use-proxy`: Use proxy settings from .env file
- `--disable-images`: Disable images for faster loading
- `--screenshot`: Take screenshots of search results pages

## Scheduled Scraping

For continuous monitoring, you can use the scheduler to check flights at regular intervals:

1. Configure your routes in `routes.json`:
   ```json
   [
     {
       "origin": "SFO",
       "destination": "NRT",
       "description": "San Francisco to Tokyo"
     }
   ]
   ```

2. Run the scheduler:
   ```bash
   python scheduler.py --routes routes.json --interval 12 --headless
   ```

The scheduler will check each route every `interval` hours (default: 24).

### Scheduler Options

- `--routes`: Path to routes JSON file - Required
- `--interval`: Job interval in hours (default: 24)
- `--months-ahead`: Number of months ahead to search (default: 3)
- `--min-duration`: Minimum flight duration in hours (default: 6)
- `--min-stay`: Minimum stay duration in days (default: 7)
- `--max-stay`: Maximum stay duration in days (default: 14)
- `--sort-by`: Sort results by this field (default: price_per_hour)
- `--limit`: Limit number of results (default: 20)
- `--headless`: Run browser in headless mode
- `--use-proxy`: Use proxy settings from .env file
- `--disable-images`: Disable images for faster loading
- `--screenshots`: Take screenshots of search results

## Data Visualization

Analyze your flight data with the included visualization tools:

```bash
python visualize.py --all
```

This will generate visualization charts for all saved flight data.

Options:
- `--file`: Visualize a specific data file (e.g., `--file data/JFK_to_LHR_20230101_120000.json`)
- `--all`: Generate visualizations for all data files
- `--output-dir`: Directory to save visualization files (default: 'visualizations')

## Proxy Support

To use a proxy for scraping:

1. Configure proxy settings in your .env file:
   ```
   USE_PROXY=true
   PROXY_HOST=your-proxy-host
   PROXY_PORT=your-proxy-port
   PROXY_USER=your-username (optional)
   PROXY_PASS=your-password (optional)
   ```

2. Enable proxy use with the `--use-proxy` flag:
   ```bash
   python main.py --origin SFO --destination NRT --use-proxy
   ```

## Results

Results are saved in the `data` directory as both JSON and CSV files, named with the format:
`{origin}_to_{destination}_{timestamp}.json/csv`

## Notes

- Google Flights may detect and block automated scraping. The scraper includes several anti-detection measures but may still get blocked.
- To minimize blocking risk, use reasonable time delays between requests.
- Consider using a proxy or VPN if you experience blocking.
- This tool is for educational purposes only.

## Disclaimer

This tool is for personal use only. Using this tool may violate Google's Terms of Service. The author takes no responsibility for any consequences of using this tool.

## License

MIT 