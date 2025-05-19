#!/usr/bin/env python3
"""
Test flight deal email format
"""

from scrapers.email_sender import EmailSender

def test_flight_deal():
    # Email configuration
    sender_email = "aleczooyork@gmail.com"
    sender_password = "vjgd inkg gjle ksmv"
    recipient_email = "alec.dc29@gmail.com"
    
    # Initialize email sender
    email_sender = EmailSender(sender_email, sender_password)
    
    # Create a sample flight deal
    sample_flight = {
        "price": 1299.99,
        "cabin_class": "Business",
        "airlines": ["Air France", "KLM"],
        "duration_hours": 8.5,
        "departure_time": "10:30 AM",
        "arrival_time": "1:45 PM",
        "departure_airport": "CDG",
        "arrival_airport": "JFK",
        "stops": 0,
        "price_per_hour": 152.94,
        "is_good_deal": True,
        "discount_percentage": 45.5,
        "departure_date": "2024-06-15",
        "return_date": "2024-06-22"
    }
    
    # Send the test flight deal
    success = email_sender.send_flight_deals(
        recipient_email=recipient_email,
        flights=[sample_flight],
        origin="CDG",
        destination="JFK",
        departure_date="2024-06-15",
        return_date="2024-06-22",
        subject_prefix="TEST: Flight Deal Format",
        highlight_deals=True
    )
    
    if success:
        print("✅ Test flight deal email sent successfully!")
        print("Check your email at alec.dc29@gmail.com to see the format.")
    else:
        print("❌ Failed to send test flight deal email.")

if __name__ == "__main__":
    test_flight_deal() 