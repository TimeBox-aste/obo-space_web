from flask import Blueprint, request, jsonify
from pika import BlockingConnection, ConnectionParameters, PlainCredentials
import json
import threading
import time
import uuid
from datetime import datetime
import settings
from core.connector.rmq_connector import RabbitMQClient

endpoint = Blueprint('api_bluep', __name__)

# RabbitMQ configuration
RABBITMQ_CONFIG = settings.RABBITMQ_CONFIG

# Create instance
rabbitmq_client = RabbitMQClient(RABBITMQ_CONFIG)

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
                'message': 'Registration submitted successfully! Check your email for further instructions.'
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

@endpoint.route('/api/v1/check-status/<registration_id>', methods=['GET'])
def check_status(registration_id):
    """Check registration status IGNORE THAT METHOD LEGACY"""
    try:
        
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