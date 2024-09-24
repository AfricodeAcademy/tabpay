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
        user_datastore.find_or_create_role(name='SuperUser',description='Account owner')
      

        #Create SuperUser
        if not user_datastore.find_user(email='enockbett427@gmail.com'):
            hashed_password = hash_password('123456')
            user_datastore.create_user(email='enockbett427@gmail.com',password=hashed_password,full_name='Captain Bett',roles=[user_datastore.find_role('SuperUser')])
            db.session.commit()
            print('Superuser created successfully')

 

    return app
