#!/usr/bin/env python3
"""
Flight Data Visualization Tool

This script generates visualizations from the flight data stored in the data directory.
"""

import os
import json
import argparse
import glob
from utils.visualization import create_dashboard

def list_data_files():
    """List all available data files in the data directory"""
    data_dir = 'data'
    if not os.path.exists(data_dir):
        print("No data directory found. Run the scraper first to generate data.")
        return []
    
    json_files = glob.glob(os.path.join(data_dir, '*.json'))
    return json_files

def load_data(file_path):
    """Load flight data from a JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading data file: {str(e)}")
        return []

def extract_route_info(filename):
    """Extract origin and destination from filename"""
    # Expected format: ORIGIN_to_DESTINATION_TIMESTAMP.json
    try:
        basename = os.path.basename(filename)
        parts = basename.split('_to_')
        origin = parts[0]
        destination = parts[1].split('_')[0]
        return origin, destination
    except:
        return "Unknown", "Unknown"

def main():
    parser = argparse.ArgumentParser(description='Flight Data Visualization Tool')
    parser.add_argument('--file', help='Specific data file to visualize')
    parser.add_argument('--all', action='store_true', help='Visualize all data files')
    parser.add_argument('--output-dir', default='visualizations', help='Directory to save visualizations')
    
    args = parser.parse_args()
    
    # List available data files if needed
    data_files = list_data_files()
    if not data_files:
        print("No data files found to visualize.")
        return
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    if args.file:
        # Visualize a specific file
        if not os.path.exists(args.file):
            print(f"File not found: {args.file}")
            return
        
        data = load_data(args.file)
        if not data:
            print(f"No data found in {args.file}")
            return
        
        origin, destination = extract_route_info(args.file)
        print(f"Visualizing data for route: {origin} to {destination}")
        
        charts = create_dashboard(data, origin, destination, args.output_dir)
        
        if charts:
            print(f"Generated {len(charts)} visualizations:")
            for chart in charts:
                print(f"  - {chart}")
        else:
            print("No visualizations could be generated from the data.")
            
    elif args.all:
        # Visualize all data files
        print(f"Found {len(data_files)} data files to visualize")
        
        for file_path in data_files:
            data = load_data(file_path)
            if not data:
                print(f"Skipping {file_path} - no data found")
                continue
            
            origin, destination = extract_route_info(file_path)
            print(f"Visualizing data for route: {origin} to {destination}")
            
            charts = create_dashboard(data, origin, destination, args.output_dir)
            
            if charts:
                print(f"  Generated {len(charts)} visualizations")
            else:
                print("  No visualizations could be generated from the data.")
    else:
        # List available files if no specific action was requested
        print("Available data files:")
        for i, file_path in enumerate(data_files, 1):
            origin, destination = extract_route_info(file_path)
            print(f"  {i}. {origin} to {destination}: {os.path.basename(file_path)}")
        
        print("\nUse --file <filename> to visualize a specific file")
        print("Use --all to visualize all files")

if __name__ == "__main__":
    main() 