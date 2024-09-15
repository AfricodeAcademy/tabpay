from flask import Flask
# from flask_migrate import Migrate
from flask_restful import Api
from app.api.api import Users,User,Communications,Communication,Payments,Payment,Blocks,Block,Umbrellas,Umbrella,Zones,Zone
from .extensions import db

def create_app():
    app = Flask(__name__)

    # Configure SQLAlchemy
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1816@localhost:5432/tabpay'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tabpay.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    # migrate = Migrate(app,db)
    # migrate.init_app(app)

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
