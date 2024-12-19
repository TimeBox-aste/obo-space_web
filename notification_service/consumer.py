import json
import logging
import time
import traceback
from typing import Dict, Any
import uuid  # Add this import at the top

from pika import PlainCredentials, BlockingConnection, ConnectionParameters
from pika.exceptions import AMQPConnectionError

from core.connector.postgresql_connector import db_operation
from core.email.email_sender import EmailSender
from settings import RABBITMQ_CONFIG
from sqlalchemy.orm import Session
from core.db.models import UserData, CopyShared, Notifications
from core.db.utils import create_user, get_user_by_email
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmailConsumer:
    def __init__(self):
        self.email_sender = EmailSender()
        self.connection = None
        self.channel = None
        self.retry_delay = 60  # 1 minute between retries

    def connect(self):
        """Establish connection to RabbitMQ"""
        if not self.connection or self.connection.is_closed:
            credentials = PlainCredentials(
                RABBITMQ_CONFIG['username'],
                RABBITMQ_CONFIG['password']
            )
            self.connection = BlockingConnection(
                ConnectionParameters(
                    host=RABBITMQ_CONFIG['host'],
                    port=RABBITMQ_CONFIG['port'],
                    credentials=credentials
                )
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(
                queue=RABBITMQ_CONFIG['queue_name'],
                durable=True
            )

    @db_operation(is_async=False)
    def process_message(self, message_data: Dict[str, Any], session: Session) -> None:
        """Process received message and handle email sending with retries"""

        
        """
        sample message_data:
        {'full_name': 'Ковалёв Евгений', 'email': 'ao.200390@gmail.com', 'accept_license': True, 'accept_age': True, 'timestamp': '2024-12-18T21:08:49.865883'}
        """

        email = message_data.get('email')
        full_name = message_data.get('full_name')
        
        if not email:
            logger.error(f"Invalid message format: {message_data}")
            return

        # Check for existing user or create new one
        user = get_user_by_email(email, session)
        if not user:
            user = create_user(
                user_data={
                    'email': email,
                    'nickname': full_name
                },
                session=session
            )
            session.add(user)
            session.flush()  # Flush to get the user.id

        # Check for existing CopyShared or create new one
        copy_share = session.query(CopyShared).filter(CopyShared.id_user == user.id).first()
        if not copy_share:
            copy_share = CopyShared(
                id_user=user.id,
                name_file_uuid=str(uuid.uuid4())
            )
            session.add(copy_share)
            session.commit()
        
        notification = Notifications(
            id_copy_shared=copy_share.id,
            id_status_sending=1
        )
        session.add(notification)
        session.commit()

        # return copy_share.uuid

    def callback(self, ch, method, properties, body):
        """Callback function for processing received messages"""
        try:
            message_data = json.loads(body)
            logger.info(f"Received message: {message_data}")
            
            self.process_message(message_data)
            
            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {body}"+("\n".join([
                    "-"*10,
                    str(e),
                    str(traceback.format_exc()),
                    "-"*10,
                ])))
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error processing message: "+("\n".join([
                    "-"*10,
                    str(e),
                    str(traceback.format_exc()),
                    "-"*10,
                ])))
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self):
        """Start consuming messages from the queue"""
        while True:
            try:
                self.connect()
                self.channel.basic_qos(prefetch_count=1)
                self.channel.basic_consume(
                    queue=RABBITMQ_CONFIG['queue_name'],
                    on_message_callback=self.callback
                )
                
                logger.info("Started consuming messages...")
                self.channel.start_consuming()
                
            except AMQPConnectionError:
                logger.error("Connection to RabbitMQ failed. Retrying in 5 seconds...")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}"+("\n".join([
                    "-"*10,
                    str(e),
                    str(traceback.format_exc()),
                    "-"*10,
                ])))
                time.sleep(5)
            finally:
                if self.connection and not self.connection.is_closed:
                    self.connection.close()

if __name__ == "__main__":
    consumer = EmailConsumer()
    consumer.start_consuming()
