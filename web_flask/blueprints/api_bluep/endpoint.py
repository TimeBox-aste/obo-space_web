from flask import Blueprint, request, jsonify
from pika import BlockingConnection, ConnectionParameters, PlainCredentials
import json
import threading
import time
import uuid
from datetime import datetime
import settings
endpoint = Blueprint('api_bluep', __name__)

# RabbitMQ configuration
RABBITMQ_CONFIG = settings.RABBITMQ_CONFIG

class RabbitMQClient:
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

class RegistrationProcessor:
    def __init__(self, rabbitmq_config):
        self.processing = False
        self.rabbitmq_client = RabbitMQClient(rabbitmq_config)
        
    def start(self):
        """Start the registration processor"""
        if not self.processing:
            self.processing = True
            thread = threading.Thread(target=self.process_queue)
            thread.daemon = True
            thread.start()

    def process_queue(self):
        """Process messages from the queue"""
        while self.processing:
            try:
                self.rabbitmq_client.connect()
                
                def callback(ch, method, properties, body):
                    try:
                        data = json.loads(body)
                        registration_id = properties.message_id
                        self.process_registration(data, registration_id)
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as e:
                        print(f"Error processing message: {str(e)}")
                        ch.basic_nack(delivery_tag=method.delivery_tag)

                self.rabbitmq_client.channel.basic_qos(prefetch_count=1)
                self.rabbitmq_client.channel.basic_consume(
                    queue=RABBITMQ_CONFIG['queue_name'],
                    on_message_callback=callback
                )
                
                print("Started consuming messages...")
                self.rabbitmq_client.channel.start_consuming()

            except Exception as e:
                print(f"Queue processing error: {str(e)}")
                time.sleep(5)

    def process_registration(self, data, registration_id):
        """Process a registration request"""
        # Add registration processing logic here
        print(f"Processing registration {registration_id} for: {data['email']}")
        time.sleep(2)  # Simulate processing

# Create instances
rabbitmq_client = RabbitMQClient(RABBITMQ_CONFIG)
registration_processor = RegistrationProcessor(RABBITMQ_CONFIG)

@endpoint.route('/api/v1/register', methods=['POST'])
def register():
    """Handle registration form submission"""
    try:
        data = {
            'full_name': request.json.get('full_name'),
            'email': request.json.get('email'),
            'accept_license': request.json.get('accept_license'),
            'accept_age': request.json.get('accept_age'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Validate required fields
        if not all([data['full_name'], data['email'], 
                   data['accept_license'], data['accept_age']]):
            return jsonify({
                'success': False,
                'message': 'All fields are required'
            }), 400

        # Send to RabbitMQ queue
        if rabbitmq_client.publish(data):
            return jsonify({
                'success': True,
                'message': 'Registration submitted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Error processing registration'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@endpoint.route('/api/v1/start-processor', methods=['POST'])
def start_processor():
    """Start the registration processor"""
    try:
        registration_processor.start()
        return jsonify({
            'success': True,
            'message': 'Processor started successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@endpoint.route('/api/v1/check-status/<registration_id>', methods=['GET'])
def check_status(registration_id):
    """Check registration status"""
    try:
        # This would typically check a database
        # Mock response for now
        return jsonify({
            'success': True,
            'registration_id': registration_id,
            'status': 'pending',
            'message': 'Registration is being processed'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500