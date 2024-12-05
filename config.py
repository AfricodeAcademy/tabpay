import os
import secrets
from datetime import timedelta
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
class Config:
    SECRET_KEY = secrets.token_hex(32)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECURITY_PASSWORD_SALT = secrets.token_hex(16)
    
    # Flask-Security settings
    SECURITY_REGISTERABLE = True
    SECURITY_CONFIRMABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_POST_LOGOUT_VIEW = '/'
    SECURITY_POST_REGISTER_VIEW = '/auth/login'
    SECURITY_URL_PREFIX = '/auth'
    SECURITY_TEMPLATE_PATH = "templates/security"
    
    # Enhanced Security Settings
    SECURITY_PASSWORD_COMPLEXITY_CHECKER = 'zxcvbn'
    SECURITY_PASSWORD_LENGTH_MIN = 8
    SECURITY_UNAUTHORIZED_VIEW = '/auth/login'
    SECURITY_SEND_REGISTER_EMAIL = True
    SECURITY_FRESHNESS = timedelta(minutes=15)
    SECURITY_FRESHNESS_GRACE_PERIOD = timedelta(hours=1)
    
    # Session Management
    SECURITY_TOKEN_AUTHENTICATION_HEADER = 'Authentication-Token'
    SECURITY_TOKEN_AUTHENTICATION_KEY = 'auth_token'
    SECURITY_TOKEN_MAX_AGE = 60 * 60 * 24  # 24 hours
    SECURITY_VERIFY_SALT = '654321098765432109876543210987654321098765'
    
    # Token Settings
    SECURITY_RESET_SALT = '123456789012345678901234567890123456789012'
    SECURITY_CONFIRM_SALT = '098765432109876543210987654321098765432109'
    SECURITY_REMEMBER_SALT = '432109876543210987654321098765432109876543'
    
    # CSRF Settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    SECURITY_CSRF_ENABLE = True
    SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS = True
    
    # Session settings
    SESSION_TYPE = 'filesystem'
    SESSION_COOKIE_NAME = 'tabpay_session'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_REFRESH_EACH_REQUEST = True
    
    # Cookie settings
    REMEMBER_COOKIE_NAME = 'tabpay_remember'
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_REFRESH_EACH_REQUEST = True
    
    # Other security settings
    SECURITY_CHANGE_EMAIL = True
    SECURITY_CHANGEABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_SALT_LENGTH = 32
    SECURITY_HASHING_SCHEMES = ['bcrypt']
    SECURITY_DEPRECATED_HASHING_SCHEMES = []
    
    # Babel configuration
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    BABEL_TRANSLATION_DIRECTORIES = 'translations'
    
    # Configuration for Zoho Mail
    MAIL_SERVER = 'smtp.zoho.com'
    MAIL_PORT = 465
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'admissions@africodeacademy.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'dtvjbPBrMfyw')  # Set this via environment variable
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME', 'admissions@africodeacademy.com')
    # Configuration for Africastalking API
    AT_USERNAME='africode'
    AT_API_KEY='atsk_26b6fd63c4ab81592df201a60a3b3c3b221234128dc34046355f0cd9198e1a7afc6e724a'
    AT_SENDER_ID='Africode'
    # M-Pesa Configuration
    MPESA_ENVIRONMENT = os.getenv('MPESA_ENVIRONMENT', 'production')
    MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
    MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
    MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
    MPESA_PASSKEY = os.getenv('MPESA_PASSKEY') 
    MPESA_STK_PUSH_SHORTCODE = os.getenv('MPESA_STK_PUSH_SHORTCODE')
    MPESA_STK_PUSH_PASSKEY = os.getenv('MPESA_STK_PUSH_PASSKEY')
    
    # M-Pesa Callback URLs
    MPESA_CALLBACK_BASE_URL = os.getenv('MPESA_CALLBACK_BASE_URL')
    MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL')
    MPESA_STK_CALLBACK_URL = os.getenv('MPESA_STK_CALLBACK_URL')
    MPESA_VALIDATION_URL = os.getenv('MPESA_VALIDATION_URL')
    MPESA_CONFIRMATION_URL = os.getenv('MPESA_CONFIRMATION_URL')
    
    # Validate required environment variables with debugging
    missing_vars = []
    env_vars = {
        'MPESA_CONSUMER_KEY': MPESA_CONSUMER_KEY,
        'MPESA_CONSUMER_SECRET': MPESA_CONSUMER_SECRET,
        'MPESA_PASSKEY': MPESA_PASSKEY,
        'MPESA_SHORTCODE': MPESA_SHORTCODE,
        'MPESA_CALLBACK_URL': MPESA_CALLBACK_URL,
        'MPESA_STK_CALLBACK_URL': MPESA_STK_CALLBACK_URL,
        'MPESA_VALIDATION_URL': MPESA_VALIDATION_URL,
        'MPESA_CONFIRMATION_URL': MPESA_CONFIRMATION_URL
    }
    
    print("Current environment variables status:")
    for var_name, var_value in env_vars.items():
        if not var_value:
            missing_vars.append(var_name)
            print(f"Missing: {var_name}")
        else:
            print(f"Found: {var_name[0]}{'*' * (len(var_name) - 1)}")
    
    if missing_vars:
        error_msg = f"Missing required M-Pesa configurations: {', '.join(missing_vars)}. Check your .env file."
        print(f"Error: {error_msg}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Environment file location: {os.path.join(os.getcwd(), '.env')}")
        raise ValueError(error_msg)
    # API Base URL from environment variable
    API_BASE_URL = os.getenv('API_BASE_URL', 'https://tabpay.africa')  # Default to production URL if not set
    # Flask-Admin settings
    FLASK_ADMIN_SWATCH = 'cyborg'
    FLASK_ADMIN_FLUID_LAYOUT = True
    ADMIN_NAME = 'TabPay Admin'
    ADMIN_TEMPLATE_MODE = 'bootstrap4'
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///tabpay.db'
    WTF_CSRF_CHECK_DEFAULT = False  # Required by Flask-Security when using SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS
    WTF_CSRF_ENABLED = True
    WTF_CSRF_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    SESSION_COOKIE_SECURE = False  # Set to False for development
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'tabpay_session'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SECURITY_CSRF_COOKIE = {'key': 'csrf_token', 'httponly': False, 'samesite': 'Lax', 'secure': False}
    SECURITY_CSRF_COOKIE_NAME = 'tabpay_csrf_token'
    SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS = True
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://tabpay:tabpay@localhost:5432/tabpay')
    
    # Security settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', 'your-salt-here')
    
    # Session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_DOMAIN = '.tabpay.africa'
    SESSION_COOKIE_NAME = 'tabpay_session'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # Flask-Security settings
    SECURITY_TOKEN_AUTHENTICATION_HEADER = 'Authentication-Token'
    SECURITY_TOKEN_MAX_AGE = 86400  # 24 hours
    SECURITY_TRACKABLE = True
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_DEFAULT_REMEMBER_ME = True
    SECURITY_TOKEN_AUTHENTICATION_KEY = 'auth_token'
    
    # Flask-Security CSRF settings
    SECURITY_CSRF_ENABLE = True
    SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS = True
    SECURITY_CSRF_COOKIE = {
        'key': 'csrf_token',
        'httponly': False,
        'samesite': 'Lax',
        'secure': True,
        'domain': '.tabpay.africa'
    }
    SECURITY_CSRF_COOKIE_NAME = 'tabpay_csrf_token'
    SECURITY_CSRF_PROTECT_MECHANISMS = ['session', 'basic']
    
    # Remember Me settings.
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_NAME = 'tabpay_remember_token'
    REMEMBER_COOKIE_DOMAIN = '.tabpay.africa'
    
    # CSRF settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = False
    WTF_CSRF_SSL_STRICT = True
    WTF_CSRF_TIME_LIMIT = 3600
    WTF_CSRF_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use in-memory SQLite for testing
    WTF_CSRF_ENABLED = False
    SECURITY_PASSWORD_HASH = 'plaintext'  # For faster testing
    SERVER_NAME = 'localhost:5000'  # Required for URL generation in tests
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,  # Add testing config
    'default': DevelopmentConfig
}