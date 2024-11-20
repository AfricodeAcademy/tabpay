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
    

    # Initialize CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    
    security.init_app(app, user_datastore,
                      template_folder="templates/security",
                     confirm_register_form=ExtendedConfirmRegisterForm,
                     register_form=ExtendedRegisterForm,
                     login_form=ExtendedLoginForm)
    
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
        
        # Create Superuser
        if not user_datastore.find_user(email='enockbett427@gmail.com'):
            hashed_password = hash_password('123456')
            user_datastore.create_user(
                email='enockbett427@gmail.com',
                password=hashed_password,
                id_number=42635058,
                full_name='Enock Bett',
                phone_number='0105405050',
                roles=[user_datastore.find_role('SuperUser')],
            is_approved=True)

            db.session.commit()
            print(f'SuperUser created successfully {user_datastore.find_user(is_approved=True)}')
            
    import_initial_banks(app)
     # Initialize debug CSRF if in debug mode
    return app

# TODODELETE HAO USERS DURING PRODUCTION ENVIRONMENT