import os
import secrets 
from datetime import timedelta

class Config:
    SECRET_KEY =  secrets.token_hex(16)
    # SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/tabpay'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///tabpay.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECURITY_PASSWORD_SALT = '201343284857125688191020663358661879047'
    SECURITY_REGISTERABLE = True
    SECURITY_POST_LOGIN_VIEW = '/statistics'
    SECURITY_POST_LOGOUT_VIEW = '/'
    SECURITY_POST_REGISTER_VIEW = '/login'
    SECURITY_CONFIRMABLE = True
    SECURITY_RECOVERABLE = True

    SESSION_COOKIE_SECURE = True  # For HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)


    # Cookie settings
    REMEMBER_COOKIE_SAMESITE = 'strict' #server side
    SESSION_COOKIE_SAMESITE = 'strict' # client side



    # Configuration for Gmail's SMTP server
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USERNAME = 'enockbett427@gmail.com' 
    MAIL_PASSWORD = 'ekpm scdy pcgy fyfz'     
    MAIL_USE_TLS = True
    MAIL_DEFAULT_SENDER = 'enockbett427@gmail.com'

    SECURITY_CHANGE_EMAIL = True
    AT_USERNAME='africode'
    AT_API_KEY='atsk_26b6fd63c4ab81592df201a60a3b3c3b221234128dc34046355f0cd9198e1a7afc6e724a'
    AT_SENDER_ID='Africode'

     # Flask-Admin config
    FLASK_ADMIN_SWATCH = 'cerulean'
    FLASK_ADMIN_FLUID_LAYOUT = True 
    SECURITY_URL_PREFIX = '/auth'

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT= 3600  
    WTF_CSRF_SECRET_KEY= SECRET_KEY
    WTF_CSRF_CHECK_DEFAULT = False

    ADMIN_NAME = 'TabPay Admin',
    ADMIN_TEMPLATE_MODE = 'bootstrap4',


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///tabpay.db'
    # SQLALCHEMY_DATABASE_URI = 'postgresql://captain:captain@localhost:5432/tabpay'
    API_BASE_URL = "http://localhost:5002" 




class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}