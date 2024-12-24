import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import logging
import threading

from settings import (
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    SENDER_EMAIL,
    BASE_URL
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EmailSender:
    """
    Email sender for sending emails

    >>> email_sender = EmailSender()
    >>> email_sender.send_registration_email('test@exist_email.com', '1234567890')
    True
    >>> email_sender.send_registration_email('test@not_exist_email.com', '1234567890')
    False

    """
    def __init__(self):
        template_dir = Path(__file__).parent / 'templates'
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.logger = logging.getLogger(__name__)
        
    def _create_message(self, to_email: str, subject: str, html_content: str) -> MIMEMultipart:
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = SENDER_EMAIL
        message['To'] = to_email
        
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        return message
    
    def send_registration_email(self, to_email: str, uuid: str) -> bool:
        """
        Send registration email with verification link
        
        Args:
            to_email: Recipient email address
            uuid: Unique identifier for the registration
            status: Optional status message
        
        Returns:
            bool: True if email was sent successfully
        """
        def timeout_handler():
            raise Exception("Email sending took too long")

        try:
            # Set a timer for 10 seconds
            timer = threading.Timer(10, timeout_handler)
            timer.start()
            
            template = self.env.get_template('registration_email.html')
            download_link = f"{BASE_URL}/download/{uuid}"
            
            html_content = template.render(
                verification_link=download_link,
                BASE_URL=BASE_URL
            )
            
            subject = "Скачайте бета-версию игры"
            message = self._create_message(to_email, subject, html_content)
            
            self.logger.info(f"Sending registration email to {to_email} with UUID {uuid}")
            
            # Add timeout for SMTP operations
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                # if server.has_extn('STARTTLS'):  # Check if TLS is supported
                #     server.starttls()
                #     server.ehlo()  # Need to say hello again after TLS
                try:
                    server.starttls()
                    server.ehlo()
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                except smtplib.SMTPAuthenticationError:
                    self.logger.error("SMTP authentication failed")
                    return False
                
                try:
                    server.send_message(message)
                except smtplib.SMTPException as e:
                    self.logger.error(f"Failed to send message: {str(e)}")
                    return False
                
            # Cancel the timer if email is sent successfully
            timer.cancel()
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email: {str(e)}")
            return False