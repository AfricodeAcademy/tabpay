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

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, UserModel, RoleModel)

def create_app(config_name):
    app = Flask(__name__)
    csrf = CSRFProtect(app)
    
    # Use the config dictionary to load the appropriate config class
    app.config.from_object(config[config_name])
    
    # Add Flask-Admin specific configurations
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    app.config['FLASK_ADMIN_FLUID_LAYOUT'] = True 
    app.config['SECURITY_URL_PREFIX'] = '/auth'
    
    
    csrf.init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    
    security.init_app(app, user_datastore,
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
    
    
    with app.app_context():
        db.create_all()
        
        # Create roles
        user_datastore.find_or_create_role(name='SuperUser', description='System Manager')
        user_datastore.find_or_create_role(name='Administrator', description='Account Owner and Umbrella creator')
        user_datastore.find_or_create_role(name='Chairman', description='Block chairman')
        user_datastore.find_or_create_role(name='Secretary', description='Block secretary')
        user_datastore.find_or_create_role(name='Member', description='Regular member')
        user_datastore.find_or_create_role(name='Treasurer', description='Block Treasurer')
        
        # Create Admin user (your existing code.)
        if not user_datastore.find_user(email='biikate48@gmail.com'):
            hashed_password = hash_password('123456')
            user_datastore.create_user(
                email='biikate48@gmail.com',
                password=hashed_password,
                id_number=42635058,
                full_name='Benard Ronoh',
                phone_number='0708665444',
                roles=[user_datastore.find_role('Administrator')]
            )

        # Create SuperUser
        if not user_datastore.find_user(email='enockbett427@gmail.com'):
            hashed_password = hash_password('123456')
            user_datastore.create_user(email='enockbett427@gmail.com', password=hashed_password,
                                       id_number=42635058, full_name='Enock Bett', phone_number='0729057932',
                                       roles=[user_datastore.find_role('SuperUser')])
            db.session.commit()
            print('SuperUser created successfully')
            
    import_initial_banks(app)
    return app