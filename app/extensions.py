from flask_sqlalchemy import SQLAlchemy
from flask_security import Security
from flask import Blueprint


db = SQLAlchemy()
security = Security()

main_blueprint = Blueprint('main', __name__,template_folder='templates',static_folder='static')
auth_blueprint = Blueprint('auth',__name__,template_folder='templates',static_folder='static' )

