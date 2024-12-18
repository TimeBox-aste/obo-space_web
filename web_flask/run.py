import logging
from core.db.utils import init_db
from settings import DATABASE_URL
from main import app
from flask import request, g

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database and get session factory
Session = init_db(DATABASE_URL)

# Add session middleware to app context
@app.before_request
def db_session_middleware():
    g.db = Session()

@app.after_request
def close_db_session(response):
    if hasattr(g, 'db'):
        g.db.commit()
        g.db.close()
    return response

@app.teardown_request
def handle_exception(exc):
    if exc and hasattr(g, 'db'):
        g.db.rollback()
    return exc

if __name__ == '__main__':
    logger.info("Starting server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
