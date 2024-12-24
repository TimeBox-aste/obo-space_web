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
Session.commit()
Session.close()
