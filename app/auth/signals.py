from flask_security import user_registered
from flask import redirect, url_for
from flask_security import current_user
from ..utils import db
import logging

def init_signals(app):
    """Initialize all signals within application context"""

    @user_registered.connect_via(app)
    def on_user_registered(sender, user, confirm_token, **extra):
        logging.debug(f"User {user.email} registered. Setting is_approved to False.")
        user.is_approved = False
        db.session.commit()

# def custom_login_response():
#     """Custom login response function for redirecting based on role."""
    
#     # Redirect based on role
#     if current_user.has_role('SuperUser'):
#         return redirect(url_for('/admin/'))
#     elif current_user.has_role('Administrator'):
#         return redirect(url_for('main.statistics'))
#     # Default redirection if no specific role
