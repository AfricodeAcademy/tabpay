from flask_sqlalchemy import SQLAlchemy
from flask_security import Security
# from flask import Blueprint
from flask_mailman import Mail

db = SQLAlchemy()
security = Security()
mail = Mail()

# main_blueprint = Blueprint('main', __name__,template_folder='templates',static_folder='static')
# auth_blueprint = Blueprint('auth',__name__,template_folder='templates',static_folder='static' )

