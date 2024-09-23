import os
import secrets 
# from .forms.auth import ExtendedRegisterForm

SECRET_KEY =  secrets.token_hex(16)
# SQLALCHEMY_DATABASE_URI = 'postgresql://captain:captain@localhost:5432/tabpay'
SQLALCHEMY_DATABASE_URI = 'sqlite:///tabpay.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECURITY_PASSWORD_SALT = '201343284857125688191020663358661879047'
SECURITY_REGISTERABLE = True
# SECURITY_REGISTER_FORM = ExtendedRegisterForm
SECURITY_POST_LOGIN_VIEW = '/statistics'
SECURITY_POST_LOGOUT_VIEW = '/'
SECURITY_POST_REGISTER_VIEW = '/login'
SECURITY_CONFIRMABLE = True
SECURITY_RECOVERABLE = True


# Cookie settings
REMEMBER_COOKIE_SAMESITE = 'strict' #server side
SESSION_COOKIE_SAMESITE = 'strict' # client side



# Configuration for Gmail's SMTP server
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USERNAME = 'enockbett427@gmail.com' 
MAIL_PASSWORD = 'ypsh pumk lluj hkeu'     
MAIL_USE_TLS = True
MAIL_DEFAULT_SENDER = 'enockbett427@gmail.com'

SECURITY_CHANGE_EMAIL = True