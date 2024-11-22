from flask import Flask
from .utils import db, mail, security
from .utils.initial_banks import import_initial_banks
from .main.models import UserModel, RoleModel
from flask_security import SQLAlchemyUserDatastore
from flask_security.utils import hash_password
from config import config
from app.auth.forms import ExtendedConfirmRegisterForm, ExtendedLoginForm, ExtendedRegisterForm
from flask_wtf.csrf import CSRFProtect
from .admin import init_admin
import logging
import os
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_session import Session

# Load environment variables
load_dotenv()

# def configure_logging():
#     # Configure root logger
#     logging.basicConfig(
#         level=logging.DEBUG,
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#     )
    
#     # Configure specific loggers
#     werkzeug_logger = logging.getLogger('werkzeug')
#     werkzeug_logger.setLevel(logging.INFO)
    
#     app_logger = logging.getLogger('app')
#     app_logger.setLevel(logging.DEBUG)

# logging.getLogger('passlib').setLevel(logging.WARNING)

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, UserModel, RoleModel)

def create_app(config_name):
    # configure_logging()
    
    # Create Flask application
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(config[config_name])
    
    # Initialize Session
    Session(app)
    
    # Initialize CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # Add security headers to all responses
    @app.after_request
    def add_security_headers(response):
        if response.mimetype == "text/html":
            # Set security headers
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['X-Content-Type-Options'] = 'nosniff'
        return response
        
    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    # Initialize Flask-Security with CSRF protection
    security.init_app(
        app,
        user_datastore,
        template_folder="templates/security",
        confirm_register_form=ExtendedConfirmRegisterForm,
        register_form=ExtendedRegisterForm,
        login_form=ExtendedLoginForm,
        csrf_cookie={"key": "csrf_token"}  # Match the config setting
    )
    
    # Ensure CSRF protection for all routes except login/register
    from flask import request
    @app.before_request
    def csrf_protect():
        if app.config['WTF_CSRF_ENABLED']:
            # Skip CSRF check for login and register endpoints
            if request.endpoint in ['security.login', 'security.register']:
                return
            csrf.protect()
    
    # Initialize Flask-Admin
    admin = init_admin(app, db)
    
    # Register blueprints
    from .main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    # Initialize signals within application context
    from app.auth.signals import init_signals
    init_signals(app)

    # Initialize Flask-RESTful API
    from app.api.api import api_bp
    csrf.exempt(api_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    from app.errors.handlers import errors as errors_blueprint
    app.register_blueprint(errors_blueprint)
    
    
    with app.app_context():
        db.create_all()

      
        # Create roles
        roles = [
            ('SuperUser', 'System Administrator'),
            ('Administrator', 'Account Owner and Umbrella creator'),
            ('Chairman', 'Block chairman'),
            ('Secretary', 'Block secretary'),
            ('Member', 'Regular member'),
            ('Treasurer', 'Block Treasurer')
        ]
        
        for role_name, description in roles:
            user_datastore.find_or_create_role(name=role_name, description=description)
        
        # Create Superusers from environment variables
        def get_superusers_from_env():
            superusers = []
            i = 1
            while True:
                email = os.getenv(f'SUPERUSER_{i}_EMAIL')
                if not email:
                    break
        
                superusers.append({
                    'email': email,
                    'password': os.getenv(f'SUPERUSER_{i}_PASSWORD'),
                    'id_number': int(os.getenv(f'SUPERUSER_{i}_ID')),
                    'full_name': os.getenv(f'SUPERUSER_{i}_NAME'),
                    'phone_number': os.getenv(f'SUPERUSER_{i}_PHONE')
                })
                i += 1
            return superusers

        superusers = get_superusers_from_env()
        
        for user_data in superusers:
            if not user_datastore.find_user(email=user_data['email']):
                hashed_password = hash_password(user_data['password'])
                user_datastore.create_user(
                    email=user_data['email'],
                    password=hashed_password,
                    id_number=user_data['id_number'],
                    full_name=user_data['full_name'],
                    phone_number=user_data['phone_number'],
                    roles=[user_datastore.find_role('SuperUser')],
                    is_approved=True
                )
                print(f"Created superuser: {user_data['email']}")
        
        db.session.commit()
        print('All superusers created successfully')

    import_initial_banks(app)
     # Initialize debug CSRF if in debug mode
    return app

# TODODELETE HAO USERS DURING PRODUCTION ENVIRONMENT