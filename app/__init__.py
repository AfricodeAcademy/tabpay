from flask import Flask, request, render_template, session, make_response, current_app
from flask_security import Security, SQLAlchemyUserDatastore, current_user
from .utils import db, mail
from .utils.initial_banks import import_initial_banks
from .main.models import UserModel, RoleModel
from flask_security.utils import hash_password
from config import config
from app.auth.forms import ExtendedConfirmRegisterForm, ExtendedLoginForm, ExtendedRegisterForm
from flask_wtf.csrf import CSRFProtect,CSRFError, generate_csrf
from .admin import init_admin
from .main.models import user_datastore
import logging
import os
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_babel import Babel
from datetime import timedelta
import uuid
import secrets
from .utils.logging_config import setup_logger
from functools import wraps

# Load environment variables
load_dotenv()

# Initialize Babel
babel = Babel()

# def get_locale():
#     # Try to guess the language from the user accept header the browser transmits
#     return request.accept_languages.best_match(['en'])

def configure_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.INFO)
    app_logger = logging.getLogger('app')
    app_logger.setLevel(logging.DEBUG)
    
    # Add specific loggers for security and CSRF
    security_logger = logging.getLogger('flask_security')
    security_logger.setLevel(logging.DEBUG)
    csrf_logger = logging.getLogger('flask_wtf.csrf')
    csrf_logger.setLevel(logging.DEBUG)

logging.getLogger('passlib').setLevel(logging.WARNING)

# Custom CSRF 
class CustomCsrfProtect(CSRFProtect):
    def __init__(self):
        super(CustomCsrfProtect, self).__init__()
        self._exempt_views = set()

    def _get_csrf_token(self):
        """Get CSRF token from form, headers, or query string"""
        # Try to get token from form
        token = request.form.get('csrf_token')
        if token:
            return token
            
        # Try to get token from headers
        token = request.headers.get('X-CSRFToken')
        if token:
            return token
            
        # Try to get token from query string
        return request.args.get('csrf_token')

    def error_handler(self, reason):
        """Custom error handler for CSRF validation"""
        # Check if endpoint exists and is csrf exempt
        if request.endpoint and getattr(current_app.view_functions[request.endpoint], '_csrf_exempt', False):
            return None
            
        # Check if route is in exempt list
        if request.path in current_app.config.get('CSRF_EXEMPT_ROUTES', []):
            return None
            
        # Check if it's an M-Pesa callback
        if request.path in ['/payments/confirmation', '/payments/validation', '/api/v1/payments/stk/callback']:
            return None
            
        # Default error handling
        return super(CustomCsrfProtect, self).error_handler(reason)

    def exempt(self, view):
        """Mark a view function as being exempt from CSRF protection"""
        @wraps(view)
        def decorated_view(*args, **kwargs):
            return view(*args, **kwargs)
        self._exempt_views.add(view)
        return decorated_view

def create_app(config_name):
    # configure_logging()
    
    # Create Flask application
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
    babel.init_app(app)
    
    # Setup logging
    setup_logger()
    
    # Load environment variables into config
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY',secrets.token_hex(32))
    app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT',"a2c95d6f1e8b7c3a4d5f9e6b8f2a7c18")
    app.config['SECURITY_TOKEN_MAX_AGE'] = int(os.environ.get('SECURITY_TOKEN_MAX_AGE', 86400))
    app.config['SECURITY_DEFAULT_REMEMBER_ME'] = os.environ.get('SECURITY_DEFAULT_REMEMBER_ME', 'True').lower() == 'true'
    app.config['SECURITY_TRACKABLE'] = os.environ.get('SECURITY_TRACKABLE', 'True').lower() == 'true'
    app.config["SECURITY_PASSWORD_COMPLEXITY_CHECKER"] = None
    
    if config_name == 'production':
        app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
        app.config['SESSION_COOKIE_DOMAIN'] = os.environ.get('SESSION_COOKIE_DOMAIN', '.tabpay.africa')
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=int(os.environ.get('PERMANENT_SESSION_LIFETIME', 86400)))
    # CSRF Configuration
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    
    # Initialize CSRF protection
    csrf = CustomCsrfProtect()
    csrf.init_app(app)

    # Set CSRF configuration
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
    app.config['WTF_CSRF_SSL_STRICT'] = True
    app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    # Initialize Flask-Security with CSRF protection
    user_datastore = SQLAlchemyUserDatastore(db, UserModel, RoleModel)
    security = Security(app, user_datastore,
        template_folder="templates/security",
        confirm_register_form=ExtendedConfirmRegisterForm,
        register_form=ExtendedRegisterForm,
        login_form=ExtendedLoginForm,
        csrf_cookie={
            "key": "csrf_token",
            "httponly": False,
            "samesite": "Lax",
            "secure": config_name == 'production',
            "domain": app.config.get('SESSION_COOKIE_DOMAIN')
        }
    )

    # Set up session persistence
    @app.before_request
    def before_request():
        if current_user.is_authenticated:
            session.permanent = True
            session.modified = True
            
            # Refresh the user's authentication token if needed
            if hasattr(current_user, 'authentication_token'):
                if not current_user.authentication_token:
                    current_user.authentication_token = str(uuid.uuid4())
                    db.session.commit()

    # CSRF protection for all routes except login/register and API
    # Update the csrf_protect function
    @app.before_request 
    def csrf_protect():
        if (request.endpoint and 
            (any(route in request.path for route in app.config['CSRF_EXEMPT_ROUTES']) or
            request.endpoint.startswith('api.') or
            request.endpoint in ['security.login', 'security.register', 
                                'security.logout', 'security.forgot_password',
                                'security.reset_password', 'security.send_confirmation'])):
            return
            
        if request.method in app.config['WTF_CSRF_METHODS']:
            csrf.protect()

        # Add security headers to all responses
    @app.after_request
    def add_security_headers(response):
        if not request.endpoint or not request.endpoint.startswith('api.'):
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            # Ensure authentication token is in header for API requests
            if current_user.is_authenticated and hasattr(current_user, 'authentication_token'):
                response.headers['Authentication-Token'] = current_user.authentication_token
        return response
        
    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
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