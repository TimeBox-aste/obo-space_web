import json
import uuid
from pika import PlainCredentials, BlockingConnection, ConnectionParameters, BasicProperties
from pika.exchange_type import ExchangeType

class RabbitMQClient:
    """
    RabbitMQ client for sending messages to a queue
    >>> import settings
    >>> rmq_client = RabbitMQClient(settings.RABBITMQ_CONFIG)
    >>> rmq_client.publish(message)
    True

    >>> rmq_client.connect()
    >>> rmq_client.channel.queue_declare(queue=config['queue_name'], durable=True)
    >>> rmq_client.channel.basic_publish(exchange='', routing_key=config['queue_name'], body=json.dumps(message), properties=BasicProperties(delivery_mode=2, message_id=str(uuid.uuid4())))
    >>> rmq_client.connection.close()

    """
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.channel = None

    def connect(self):
        """Establish connection to RabbitMQ"""
        if not self.connection or self.connection.is_closed:
            credentials = PlainCredentials(
                self.config['username'], 
                self.config['password']
            )
            self.connection = BlockingConnection(
                ConnectionParameters(
                    host=self.config['host'],
                    port=self.config['port'],
                    credentials=credentials
                )
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(
                queue=self.config['queue_name'], 
                durable=True
            )

    def publish(self, message):
        """Publish message to queue"""
        try:
            self.connect()
            self.channel.basic_publish(
                exchange='',
                routing_key=self.config['queue_name'],
                body=json.dumps(message),
                properties=BasicProperties(
                    delivery_mode=2,  # make message persistent
                    message_id=str(uuid.uuid4())
                )
            )
            return True
        except Exception as e:
            print(f"Error publishing message: {str(e)}")
            return False
        finally:
            if self.connection and not self.connection.is_closed:
                self.connection.close()