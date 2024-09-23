from flask import Blueprint

auth = Blueprint('auth', __name__)

from . import routes  # Import routes to register them with the blueprint
