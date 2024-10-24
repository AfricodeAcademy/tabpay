from flask import Flask
from .utils import db, mail, security
from .main.models import UserModel, RoleModel
from flask_security import SQLAlchemyUserDatastore
from flask_security.utils import hash_password
from config import config
from app.auth.forms import ExtendedConfirmRegisterForm, ExtendedLoginForm, ExtendedRegisterForm
from flask_wtf.csrf import CSRFProtect

 # Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, UserModel, RoleModel)
def create_app(config_name):
    app = Flask(__name__)
    csrf = CSRFProtect(app)
    
    # Use the config dictionary to load the appropriate config class
    app.config.from_object(config[config_name])
    csrf.init_app(app)
    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    
    security.init_app(app, user_datastore, confirm_register_form=ExtendedConfirmRegisterForm,
                      register_form=ExtendedRegisterForm, login_form=ExtendedLoginForm)
    # Register main blueprints
    from .main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    # Register blueprints
    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    # Initialize Flask-RESTful API
    from app.api.api import api_bp
    csrf.exempt(api_bp)
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    with app.app_context():
        db.create_all()
        
        # Create roles
        user_datastore.find_or_create_role(name='Admin', description='System Administrator')
        user_datastore.find_or_create_role(name='SuperUser', description='Account Owner and Umbrella creator')
        user_datastore.find_or_create_role(name='Chairman', description='Block chairman')
        user_datastore.find_or_create_role(name='Secretary', description='Block secretary')
        user_datastore.find_or_create_role(name='Member', description='Regular member')
        user_datastore.find_or_create_role(name='Treasurer',description='Block Treasurer')
        
        # Create Admin
        if not user_datastore.find_user(email='enockbett427@gmail.com'):
            hashed_password = hash_password('123456')
            user_datastore.create_user(email='enockbett427@gmail.com', password=hashed_password,
                                       id_number=42635058, full_name='Enock Bett', phone_number='0798354820',
                                       roles=[user_datastore.find_role('Admin')])
            db.session.commit()
            print('Admin created successfully')

        # Create SuperUser
        if not user_datastore.find_user(email='captainbett77@gmail.com'):
            hashed_password = hash_password('123456')
            SuperUser_role = user_datastore.find_role('SuperUser')
            user_datastore.create_user(email='captainbett77@gmail.com', password=hashed_password,
                                       id_number=987654321, full_name='Captain',
                                        phone_number='0796533555', roles=[SuperUser_role])
            db.session.commit()
            print('SuperUser created successfully')
    
    return app