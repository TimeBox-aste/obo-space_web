import json
import time
import threading
from core.connector.rmq_connector import RabbitMQClient
from core.db.models import UserData, CopyShared, Notifications, Statuses
from core.connector.postgresql_connector import PostgreSQLConnector, db_operation
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from core.email.email_sender import EmailSender
import logging
import queue

from settings import RABBITMQ_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log_queue = queue.Queue()  # Create a queue for logging

def log_worker():
    """Thread function to handle logging."""
    while True:
        record = log_queue.get()
        if record is None:  # Exit condition
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)

# Start the logging thread
logging_thread = threading.Thread(target=log_worker)
logging_thread.start()

class RegistrationProcessor:
    def __init__(self, rabbitmq_config):
        self.processing = False
        self.rabbitmq_client = RabbitMQClient(rabbitmq_config)
        self.db = PostgreSQLConnector()
        self.email_sender = EmailSender()
        
    @db_operation(is_async=False)
    def process_registration(self, data, registration_id, session: Session):
        """
        Process a registration request and store it in the database
        
        Args:
            data (dict): Registration data containing email and file information
            registration_id (str): Unique identifier for the registration
            session (Session): Database session provided by the decorator
        """
        try:
            # Check if user exists, if not create new user
            user = session.query(UserData).filter_by(email=data['email']).first()
            if not user:
                user = UserData(
                    email=data['email'],
                    nickname=data.get('nickname', data['email'].split('@')[0]),
                    is_active=True
                )
                session.add(user)
                session.flush()  # Flush to get the user ID

            # Create copy shared record
            copy_shared = CopyShared(
                id_user=user.id,
                name_file_uuid=registration_id
            )
            session.add(copy_shared)
            session.flush()

            # Get or create initial status
            initial_status = session.query(Statuses).filter_by(name='PENDING').first()
            if not initial_status:
                initial_status = Statuses(
                    name='PENDING',
                    description='Registration is being processed'
                )
                session.add(initial_status)
                session.flush()

            # Create notification record
            notification = Notifications(
                id_copy_shared=copy_shared.id,
                id_status_sending=initial_status.id,
                dt_sent=datetime.now(timezone.utc)
            )

            # Send registration email
            email_sent = self.email_sender.send_registration_email(
                to_email=data['email'],
                uuid=registration_id
            )
            
            if not email_sent:
                raise Exception("Failed to send registration email")

            session.add(notification)

            logging.info(f"Successfully processed registration {registration_id} for: {data['email']}")
            log_queue.put(logging.LogRecord('RegistrationProcessor', logging.INFO, '', 0, f"Successfully processed registration {registration_id} for: {data['email']}", None, None))
            return True

        except Exception as e:
            logging.error(f"Error processing registration: {str(e)}")
            log_queue.put(logging.LogRecord('RegistrationProcessor', logging.ERROR, '', 0, f"Error processing registration: {str(e)}", None, None))
            session.rollback()
            raise

    def update_registration_status(self, registration_id, status_name, session: Session):
        """Update the status of a registration"""
        try:
            # Get the copy shared record
            copy_shared = session.query(CopyShared).filter_by(name_file_uuid=registration_id).first()
            if not copy_shared:
                raise ValueError(f"No registration found with ID: {registration_id}")

            # Get or create status
            status = session.query(Statuses).filter_by(name=status_name).first()
            if not status:
                status = Statuses(
                    name=status_name,
                    description=f"Status: {status_name}"
                )
                session.add(status)
                session.flush()

            # Get user email from copy_shared relationship
            user_email = copy_shared.user.email

            # Send status update email
            email_sent = self.email_sender.send_registration_email(
                to_email=user_email,
                uuid=registration_id,
                status=status_name
            )
            
            if not email_sent:
                print(f"Warning: Failed to send status update email to {user_email}")

            # Create new notification with updated status
            notification = Notifications(
                id_copy_shared=copy_shared.id,
                id_status_sending=status.id,
                dt_sent=datetime.utcnow()
            )
            session.add(notification)

            logging.info(f"Updated registration {registration_id} status to {status_name}")
            log_queue.put(logging.LogRecord('RegistrationProcessor', logging.INFO, '', 0, f"Updated registration {registration_id} status to {status_name}", None, None))
            return True

        except Exception as e:
            logging.error(f"Error updating registration status: {str(e)}")
            log_queue.put(logging.LogRecord('RegistrationProcessor', logging.ERROR, '', 0, f"Error updating registration status: {str(e)}", None, None))
            session.rollback()
            raise

    def process_queue(self):
        """Process messages from the queue"""
        while self.processing:
            try:
                self.rabbitmq_client.connect()
                
                def callback(ch, method, properties, body):
                    try:
                        data = json.loads(body)
                        registration_id = properties.message_id
                        
                        with self.db.get_db() as session:
                            self.process_registration(data, registration_id, session=session)
                            # Update status to COMPLETED after successful processing
                            self.update_registration_status(
                                registration_id, 
                                'COMPLETED', 
                                session=session
                            )
                        
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as e:
                        print(f"Error processing message: {str(e)}")
                        # Update status to FAILED on error
                        with self.db.get_db() as session:
                            self.update_registration_status(
                                registration_id, 
                                'FAILED', 
                                session=session
                            )
                        ch.basic_nack(delivery_tag=method.delivery_tag)

                self.rabbitmq_client.channel.basic_qos(prefetch_count=1)
                self.rabbitmq_client.channel.basic_consume(
                    queue=RABBITMQ_CONFIG['queue_name'],
                    on_message_callback=callback
                )
                
                logging.info("Started consuming messages...")
                log_queue.put(logging.LogRecord('RegistrationProcessor', logging.INFO, '', 0, "Started consuming messages...", None, None))
                self.rabbitmq_client.channel.start_consuming()

            except Exception as e:
                logging.error(f"Queue processing error: {str(e)}")
                log_queue.put(logging.LogRecord('RegistrationProcessor', logging.ERROR, '', 0, f"Queue processing error: {str(e)}", None, None))
                time.sleep(5)

    def cleanup(self):
        """Cleanup resources"""
        self.processing = False
        self.db.dispose()
        log_queue.put(None)  # Signal the logging thread to exit
        logging_thread.join()  # Wait for the logging thread to finish

    def start(self):
        """Start the registration processor"""
        if not self.processing:
            self.processing = True
            thread = threading.Thread(target=self.process_queue)
            thread.daemon = True
            thread.start()