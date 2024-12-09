import os
import sys
import gc
import logging
import psutil
from flask_wtf.csrf import CSRFError
from dotenv import load_dotenv

# Add the application directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables before importing app
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/gunicorn/error.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def log_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    logger.info(f'Memory usage: {mem_info.rss / 1024 / 1024:.2f} MB')

try:
    # Ensure DATABASE_URL environment variable is set for production
    if 'DATABASE_URL' not in os.environ:
        logger.warning('DATABASE_URL environment variable not set!')
    
    # Create the application
    app = create_app('production')
    
    # Add memory logging to before_request
    @app.before_request
    def before_request():
        gc.collect()  # Force garbage collection
        log_memory_usage()
    
    # Add error handlers
    @app.errorhandler(500)
    def handle_500(error):
        logger.error(f'Internal Server Error: {error}')
        return 'Internal Server Error', 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        logger.warning(f'CSRF Error: {error.description}')
        return 'CSRF validation failed. Please try again.', 400
    
    logger.info('Application created successfully')
except Exception as e:
    logger.error(f'Failed to create application: {str(e)}')
    raise

if __name__ == "__main__":
    app.run()
