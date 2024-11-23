import os
import secrets
from datetime import timedelta

class Config:
    SECRET_KEY = secrets.token_hex(32)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECURITY_PASSWORD_SALT = '201343284857125688191020663358661879047'
    
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
    
    # Configuration for Gmail's SMTP server
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USERNAME = 'enockbett427@gmail.com' 
    MAIL_PASSWORD = 'ekpm scdy pcgy fyfz'     
    MAIL_USE_TLS = True
    MAIL_DEFAULT_SENDER = 'enockbett427@gmail.com'

    # Configuration for Africastalking API
    AT_USERNAME='africode'
    AT_API_KEY='atsk_26b6fd63c4ab81592df201a60a3b3c3b221234128dc34046355f0cd9198e1a7afc6e724a'
    AT_SENDER_ID='Africode'

    # M-Pesa Configuration
    MPESA_ENVIRONMENT = os.getenv('MPESA_ENVIRONMENT', 'sandbox')
    MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
    MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
    MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
    MPESA_PASSKEY = os.getenv('MPESA_PASSKEY')
    MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL')
    MPESA_CALLBACK_BASE_URL = os.getenv('MPESA_CALLBACK_BASE_URL')

    # API Base URL from environment variable
    API_BASE_URL = os.getenv('API_BASE_URL', 'https://tabpay.africa')  # Default to production URL if not set

    # Flask-Admin settings
    FLASK_ADMIN_SWATCH = 'cyborg'
    FLASK_ADMIN_FLUID_LAYOUT = True
    ADMIN_NAME = 'TabPay Admin'
    ADMIN_TEMPLATE_MODE = 'bootstrap4'


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://tabpay:tabpay@localhost:5432/tabpay'
    WTF_CSRF_CHECK_DEFAULT = False
    # API_BASE_URL is inherited from Config class

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://tabpay:tabpay@localhost:5432/tabpay')
    
    # Session settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_DOMAIN = '.tabpay.africa'
    SESSION_COOKIE_NAME = 'tabpay_session'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # CSRF settings
    SECURITY_CSRF_COOKIE = {'key': 'csrf_token', 'httponly': False, 'samesite': 'Lax', 'secure': True}
    SECURITY_CSRF_COOKIE_NAME = 'tabpay_csrf_token'
    SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS = True  # Allow login without CSRF
    WTF_CSRF_CHECK_DEFAULT = False  # Required when SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS is True
    WTF_CSRF_SSL_STRICT = True
    WTF_CSRF_ENABLED = True
    WTF_CSRF_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    # Cookie settings
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_NAME = 'tabpay_remember_token'

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
