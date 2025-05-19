#!/usr/bin/env python3
"""
Test email connectivity for the flight deal bot
"""

from scrapers.email_sender import EmailSender

def test_email():
    # Email configuration
    sender_email = "aleczooyork@gmail.com"
    sender_password = "vjgd inkg gjle ksmv"  # App Password
    recipient_email = "alec.dc29@gmail.com"
    
    # Initialize email sender
    email_sender = EmailSender(sender_email, sender_password)
    
    # Test email content
    subject = "Test Email from Flight Deal Bot"
    html_content = """
    <html>
    <body>
        <h2>Test Email</h2>
        <p>If you're receiving this email, the flight deal bot's email system is working correctly!</p>
        <p>You will receive flight deals at this email address.</p>
    </body>
    </html>
    """
    
    # Try to send the test email
    success = email_sender.send_email(
        recipient_email=recipient_email,
        subject=subject,
        html_content=html_content
    )
    
    if success:
        print("✅ Test email sent successfully!")
        print("The bot is properly configured to send emails.")
    else:
        print("❌ Failed to send test email.")
        print("\nTo fix this, please:")
        print("1. Go to your Google Account settings")
        print("2. Enable 2-Step Verification if not already enabled")
        print("3. Go to Security → App passwords")
        print("4. Generate a new app password for 'Mail'")
        print("5. Replace the EMAIL_PASSWORD in run_bot.py with the new app password")

if __name__ == "__main__":
    test_email() 