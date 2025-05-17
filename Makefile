.PHONY: setup run-example run-scraper run-scheduler clean-data clean-screenshots visualize help

help:
	@echo "Google Flights Scraper - Makefile Commands"
	@echo "----------------------------------------"
	@echo "setup             : Set up environment and install dependencies"
	@echo "run-example       : Run the example script (JFK to LHR)"
	@echo "run-scraper       : Run the scraper with default parameters"
	@echo "run-scheduler     : Run the scheduler with routes from routes.json"
	@echo "visualize         : Generate visualizations for all saved data"
	@echo "clean-data        : Remove all saved flight data"
	@echo "clean-screenshots : Remove all saved screenshots"
	@echo "help              : Show this help message"

setup:
	@echo "Setting up Google Flights Scraper..."
	pip install -r requirements.txt
	@if [ ! -f .env ]; then cp env.example .env; echo ".env file created from template"; else echo ".env file already exists"; fi
	@echo "Setup complete!"

run-example:
	@echo "Running example script..."
	python example.py

run-scraper:
	@echo "Running scraper..."
	python main.py --origin JFK --destination LHR --headless --disable-images --months-ahead 2

run-scheduler:
	@echo "Running scheduler..."
	python scheduler.py --routes routes.json --headless --disable-images --interval 24

visualize:
	@echo "Generating visualizations..."
	python visualize.py --all

clean-data:
	@echo "Cleaning data directory..."
	rm -rf data/*.json data/*.csv
	@echo "Data cleared!"

clean-screenshots:
	@echo "Cleaning screenshots directory..."
	rm -rf screenshots/*.png
	@echo "Screenshots cleared!" 