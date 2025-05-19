import smtplib
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from datetime import datetime

class EmailSender:
    def __init__(self, sender_email=None, sender_password=None, smtp_server="smtp.gmail.com", smtp_port=587):
        """
        Initialize the email sender.
        
        Args:
            sender_email (str): Sender's email address (if None, must be set with environment variable EMAIL_USER)
            sender_password (str): Sender's email password or app password (if None, must be set with environment variable EMAIL_PASSWORD)
            smtp_server (str): SMTP server address
            smtp_port (int): SMTP server port
        """
        self.sender_email = sender_email or os.environ.get("EMAIL_USER")
        self.sender_password = sender_password or os.environ.get("EMAIL_PASSWORD")
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.logger = logging.getLogger("email_sender")
        
        # Validate credentials
        if not self.sender_email or not self.sender_password:
            self.logger.warning("Email credentials not provided. Email functionality will not work.")
    
    def format_flights_html(self, flights, origin, destination, departure_date, return_date=None, sort_by="price_per_hour"):
        """
        Format flights data as HTML for email.
        
        Args:
            flights (list): List of flight dictionaries
            origin (str): Origin airport code
            destination (str): Destination airport code
            departure_date (str): Departure date
            return_date (str): Return date (optional)
            sort_by (str): How flights were sorted
            
        Returns:
            str: HTML content for email
        """
        if not flights:
            return "<p>No flights found matching your criteria.</p>"
        
        # Format header
        trip_type = "Round Trip" if return_date else "One Way"
        date_range = f"{departure_date}" + (f" to {return_date}" if return_date else "")
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #4285f4; color: white; padding: 20px; text-align: center; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 12px 15px; border-bottom: 1px solid #ddd; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:hover {{ background-color: #f5f5f5; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #777; text-align: center; }}
                .highlight {{ background-color: #e7f3fe; }}
                .price {{ font-weight: bold; color: #4285f4; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Flight Deals: {origin} to {destination}</h1>
                <p>{trip_type} | {date_range}</p>
            </div>
            <div class="container">
                <h2>Top Flight Deals (Sorted by {sort_by})</h2>
                <p>Found {len(flights)} flights that match your criteria:</p>
                
                <table>
                    <tr>
                        <th>Airline</th>
                        <th>Price</th>
                        <th>Duration</th>
                        <th>Stops</th>
                        <th>Departure</th>
                        <th>Arrival</th>
                        <th>Price/Hour</th>
                    </tr>
        """
        
        # Add rows for each flight
        for i, flight in enumerate(flights):
            airlines = ", ".join(flight["airlines"]) if isinstance(flight["airlines"], list) else flight["airlines"]
            price = f"${flight['price']:.2f}"
            duration = f"{flight['duration_hours']:.1f} hours"
            price_per_hour = f"${flight['price_per_hour']:.2f}/hr" if flight.get('price_per_hour') else "N/A"
            
            # Highlight the best deal
            row_class = "highlight" if i == 0 else ""
            
            html += f"""
                <tr class="{row_class}">
                    <td>{airlines}</td>
                    <td class="price">{price}</td>
                    <td>{duration}</td>
                    <td>{flight['stops']}</td>
                    <td>{flight['departure_airport']} ({flight['departure_time']})</td>
                    <td>{flight['arrival_airport']} ({flight['arrival_time']})</td>
                    <td>{price_per_hour}</td>
                </tr>
            """
        
        # Close the table and add footer
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html += f"""
                </table>
                
                <p>View these flights on <a href="https://www.google.com/travel/flights?q=Flights%20to%20{destination}%20from%20{origin}%20on%20{departure_date}{('%20through%20' + return_date) if return_date else ''}">Google Flights</a></p>
                
                <div class="footer">
                    <p>This email was automatically generated by Google Flights Scraper on {current_time}.</p>
                    <p>You received this because you subscribed to flight deal alerts.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_email(self, recipient_email, subject, html_content, text_content=None, attachments=None):
        """
        Send an email.
        
        Args:
            recipient_email (str): Recipient's email address
            subject (str): Email subject
            html_content (str): HTML content of the email
            text_content (str, optional): Plain text content of the email
            attachments (list, optional): List of file paths to attach
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not self.sender_email or not self.sender_password:
            self.logger.error("Email credentials not configured. Cannot send email.")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        
        # Add text content if provided, otherwise create from HTML
        if text_content is None and html_content:
            # Simple conversion of HTML to text (very basic)
            text_content = html_content.replace('<br>', '\n').replace('</p>', '\n').replace('</h1>', '\n\n').replace('</h2>', '\n\n')
            text_content = ''.join(c for c in text_content if ord(c) < 128)  # Remove non-ASCII
        
        if text_content:
            msg.attach(MIMEText(text_content, 'plain'))
        
        if html_content:
            msg.attach(MIMEText(html_content, 'html'))
        
        # Add attachments
        if attachments:
            for attachment_path in attachments:
                if os.path.exists(attachment_path):
                    with open(attachment_path, 'rb') as f:
                        file_data = f.read()
                    
                    # Determine attachment type
                    filename = os.path.basename(attachment_path)
                    if attachment_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        attachment = MIMEImage(file_data, name=filename)
                    else:
                        attachment = MIMEText(file_data.decode('utf-8'))
                        attachment.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                    
                    msg.attach(attachment)
        
        # Send email
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            self.logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def _create_flight_link(self, origin, destination, departure_date, return_date):
        """Create a Google Flights search link"""
        return f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}%20from%20{origin}%20on%20{departure_date}%20through%20{return_date}"
    
    def send_flight_deals(self, recipient_email, flights, origin, destination, departure_date, return_date, 
                         sort_by="price", screenshot_path=None, csv_path=None, subject_prefix="Flight Deals", 
                         highlight_deals=False):
        """Send flight deals via email"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject_prefix
            
            # Create HTML content
            html_content = f"""
            <html>
            <body>
            <h2>Flight Deals from {origin} to {destination}</h2>
            <p>Departure: {departure_date} - Return: {return_date}</p>
            """
            
            # Add direct Google Flights link
            flight_link = self._create_flight_link(origin, destination, departure_date, return_date)
            html_content += f'<p><a href="{flight_link}" target="_blank">View on Google Flights</a></p>'
            
            # Add flights table
            html_content += """
            <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th>Price</th>
                <th>Cabin</th>
                <th>Airlines</th>
                <th>Duration</th>
                <th>Stops</th>
                <th>Discount</th>
                <th>Link</th>
            </tr>
            """
            
            for flight in flights:
                # Create individual flight link
                flight_link = self._create_flight_link(
                    flight.get('departure_airport', origin),
                    flight.get('arrival_airport', destination),
                    flight.get('departure_date', departure_date),
                    flight.get('return_date', return_date)
                )
                
                # Style for good deals
                style = 'background-color: #e6ffe6;' if flight.get('is_good_deal', False) else ''
                
                html_content += f"""
                <tr style="{style}">
                    <td>${flight['price']:.2f}</td>
                    <td>{flight['cabin_class']}</td>
                    <td>{', '.join(flight['airlines'])}</td>
                    <td>{flight['duration_hours']:.1f}h</td>
                    <td>{flight['stops']}</td>
                    <td>{flight.get('discount_percentage', 0):.1f}%</td>
                    <td><a href="{flight_link}" target="_blank">View Deal</a></td>
                </tr>
                """
            
            html_content += """
            </table>
            <p>Note: Click the links to view the exact flights on Google Flights.</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, 'html'))
            
            # Attach screenshot if provided
            if screenshot_path and os.path.exists(screenshot_path):
                with open(screenshot_path, 'rb') as f:
                    img = MIMEApplication(f.read(), _subtype='png')
                    img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(screenshot_path))
                    msg.attach(img)
            
            # Attach CSV if provided
            if csv_path and os.path.exists(csv_path):
                with open(csv_path, 'rb') as f:
                    csv = MIMEApplication(f.read(), _subtype='csv')
                    csv.add_header('Content-Disposition', 'attachment', filename=os.path.basename(csv_path))
                    msg.attach(csv)
            
            # Send email
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            self.logger.info(f"Email sent to {recipient_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email: {str(e)}")
            return False 