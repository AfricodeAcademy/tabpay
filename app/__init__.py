from flask import Flask
from .utils import db, mail, security
from app.api.api import UserModel, Role
from flask_security import SQLAlchemyUserDatastore
from flask_security.utils import hash_password
from config import config
from app.auth.forms import ExtendedRegisterForm, ExtendedConfirmRegisterForm


def create_app(config_name):
    app = Flask(__name__)

    # Use the config dictionary to load the appropriate config class
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)

    # Setup Flask-Security
    user_datastore = SQLAlchemyUserDatastore(db, UserModel, Role)
    security.init_app(app, user_datastore, register_form=ExtendedRegisterForm, confirm_register_form=ExtendedConfirmRegisterForm)

    # Register blueprints
    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from app.main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Initialize Flask-RESTful API
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    with app.app_context():
        db.create_all()

        #Create roles
        user_datastore.find_or_create_role(name='Umbrella_creator',description='Account owner')
        user_datastore.find_or_create_role(name='Chairman',description='Head of block')
        user_datastore.find_or_create_role(name='Secretary',description='block secretary')
        user_datastore.find_or_create_role(name='Member',description='Regular member')
    

        #Create Admin
        if not user_datastore.find_user(email='enockbett427@gmail.com'):
            hashed_password = hash_password('123456')
            user_datastore.create_user(email='enockbett427@gmail.com',password=hashed_password,roles=[user_datastore.find_role('Umbrella_creator')])
            db.session.commit()
            print('Umbrella_creator created successfully')

        #Create Chairman
        if not user_datastore.find_user(email='captain@example.com'):
            hashed_password = hash_password('123456')
            user_datastore.create_user(email='captain@example.com',password=hashed_password,roles=[user_datastore.find_role('Chairman')])
            db.session.commit()

        #Create Secretary
        if not user_datastore.find_user(email='secretary@example.com'):
            hashed_password = hash_password('123456')
            user_datastore.create_user(email='secretary@example.com',password=hashed_password,roles=[user_datastore.find_role('Secretary')])
            db.session.commit()

        #Create Members
        if not user_datastore.find_user(email='member1@example.com'):
            hashed_password = hash_password('123456')
            user_datastore.create_user(email='member1@example.com',password=hashed_password,roles=[user_datastore.find_role('Member')])
            db.session.commit()

    return app
