from flask import Flask,redirect, url_for, flash, render_template
from flask_restful import Api
from app import config
from flask_restful import Api
from app.api.api import Users,User,Communications,Communication,Payments,Payment,Blocks,Block,Umbrellas,Umbrella,Zones,Zone
from flask_security import  SQLAlchemyUserDatastore
from flask_security.utils import hash_password,verify_password,login_user,logout_user
from app.models.models import UserModel, Role
from app.extensions import security, db

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    # Initialize extensions
    db.init_app(app)
    
    # Setup Flask-Security
    user_datastore = SQLAlchemyUserDatastore(db, UserModel, Role)
    security.init_app(app, user_datastore)

    # Initialize Flask-RESTful API
    api = Api(app)
    api.add_resource(Users, '/api/v1/users/')
    api.add_resource(User, '/api/v1/users/<int:id>/')
    api.add_resource(Communications, '/api/v1/communications/')
    api.add_resource(Communication, '/api/v1/communications/<int:id>/')
    api.add_resource(Payments, '/api/v1/payments/')
    api.add_resource(Payment, '/api/v1/payments/<int:id>/')
    api.add_resource(Blocks, '/api/v1/blocks/')
    api.add_resource(Block, '/api/v1/blocks/<int:id>/')
    api.add_resource(Umbrellas, '/api/v1/umbrellas/')
    api.add_resource(Umbrella, '/api/v1/umbrellas/<int:id>/')
    api.add_resource(Zones, '/api/v1/zones/')
    api.add_resource(Zone, '/api/v1/zones/<int:id>/')

    return app