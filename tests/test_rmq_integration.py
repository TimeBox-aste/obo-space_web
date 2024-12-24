"""Integration tests for RabbitMQ message publishing and consuming.

This module tests the interaction between the publisher and consumer to ensure
that messages are correctly sent and received.
"""

import json
import time
import unittest
from threading import Thread
from rmq_connector import RabbitMQClient

class TestConsumer:
    """Simple test consumer that stores received messages"""
    def __init__(self, config):
        self.config = config
        self.received_messages = []
        self.should_stop = False
        
    def callback(self, ch, method, properties, body):
        """Store received message and acknowledge it"""
        message = json.loads(body)
        self.received_messages.append(message)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    def connect(self):
        """Connect to RabbitMQ using the same connector as publisher"""
        self.client = RabbitMQClient(self.config)
        self.client.connect()
        return self.client.channel
        
    def start_consuming(self):
        """Start consuming messages"""
        channel = self.connect()
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=self.config['queue_name'],
            on_message_callback=self.callback
        )
        
        while not self.should_stop:
            self.client.connection.process_data_events(time_limit=1)
            
class TestRabbitMQIntegration(unittest.TestCase):
    """Integration tests for RabbitMQ message publishing and consuming.
    
    This class tests the interaction between the publisher and consumer to ensure
    that messages are correctly sent and received.
    """
    
    def setUp(self):
        """Setup test environment"""
        self.config = {
            'host': 'localhost',
            'port': 5672,
            'username': 'guest',
            'password': 'guest',
            'queue_name': 'test_queue'
        }
        self.publisher = RabbitMQClient(self.config)
        self.consumer = TestConsumer(self.config)
        
        self.consumer_thread = Thread(target=self.consumer.start_consuming)
        self.consumer_thread.daemon = True
        self.consumer_thread.start()
        
    def tearDown(self):
        """Cleanup after tests"""
        self.consumer.should_stop = True
        self.consumer_thread.join(timeout=1)

        channel = self.publisher.connect()
        channel.queue_purge(self.config['queue_name'])
        self.publisher.connection.close()
        
    def test_message_publishing_and_consuming(self):
        """Test that published message is received by consumer.
        
        This test verifies that a message published to the RabbitMQ queue is
        successfully consumed by the consumer.
        """
        test_message = {
            'type': 'test',
            'data': 'Hello, World!',
            'timestamp': time.time()
        }
        
        # Publish message
        success = self.publisher.publish(test_message)
        self.assertTrue(success)
        
        # Wait for message to be consumed
        max_wait = 5 
        start_time = time.time()
        while len(self.consumer.received_messages) == 0:
            if time.time() - start_time > max_wait:
                self.fail("Timeout waiting for message")
            time.sleep(0.1)
            
        # Verify received message
        self.assertEqual(len(self.consumer.received_messages), 1)
        received = self.consumer.received_messages[0]
        self.assertEqual(received['type'], test_message['type'])
        self.assertEqual(received['data'], test_message['data'])
        
if __name__ == '__main__':
    unittest.main() 