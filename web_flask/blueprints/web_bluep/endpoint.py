from flask import Blueprint, render_template

endpoint = Blueprint('web_bluep', __name__)

@endpoint.route('/')
def index():
    """Render the main index page"""
    return render_template('index.html')

@endpoint.route('/success')
def success():
    """Render success page after registration"""
    return render_template('success.html')

@endpoint.route('/status')
def status():
    """Render status check page"""
    return render_template('status.html')