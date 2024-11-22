import os
import secrets
from datetime import timedelta

class Config:
    SECRET_KEY = secrets.token_hex(32)
    # SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/tabpay'
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///tabpay.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECURITY_PASSWORD_SALT = '201343284857125688191020663358661879047'
    
    # Flask-Security settings
    SECURITY_REGISTERABLE = True
    SECURITY_CONFIRMABLE = True
    SECURITY_RECOVERABLE = True
    # Removed SECURITY_POST_LOGIN_VIEW to use our custom handler
    SECURITY_POST_LOGOUT_VIEW = '/'
    SECURITY_POST_REGISTER_VIEW = '/auth/login'
    SECURITY_URL_PREFIX = '/auth'
    SECURITY_TEMPLATE_PATH = "templates/security"
    SECURITY_CSRF_ENABLE = True
    SECURITY_CSRF_PROTECT_MECHANISMS = ['basic']  
    SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS = True  
    SECURITY_CHANGE_EMAIL = True
    SECURITY_CHANGEABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_TOKEN_MAX_AGE = 60 * 60 * 24  # 24 hours
    
    #add these for better security
    SECURITY_CSRF_COOKIE = {'httponly': True, 'samesite': 'Lax', 'secure': False}
    SECURITY_CSRF_COOKIE_NAME = 'csrf_token'

    # Session settings
    SESSION_COOKIE_SECURE = False  
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'  
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)  
    SESSION_PROTECTION = 'strong'
    
    # Cookie settings
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'  
    
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

    # CSRF settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  
    WTF_CSRF_SECRET_KEY = SECRET_KEY
    WTF_CSRF_CHECK_DEFAULT = False
    WTF_CSRF_SSL_STRICT = False


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://tabpay:tabpay@localhost:5432/tabpay'
    # API_BASE_URL is inherited from Config class

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://tabpay:tabpay@localhost:5432/tabpay')
    
    # Session and security settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_DOMAIN = '.tabpay.africa'
    SESSION_COOKIE_NAME = 'tabpay_session'  # Custom session name
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # CSRF settings
    SECURITY_CSRF_COOKIE = {'httponly': True, 'samesite': 'Lax', 'secure': True}
    SECURITY_CSRF_COOKIE_NAME = 'tabpay_csrf_token'  # Custom CSRF token name
    SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS = False
    WTF_CSRF_SSL_STRICT = True
    WTF_CSRF_ENABLED = True
    WTF_CSRF_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    # Cookie settings
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_NAME = 'tabpay_remember_token'  # Custom remember token name

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
