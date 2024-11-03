from flask_security import user_registered
from flask import current_app #Fix for "RuntimeError: Working outside of application context."
from .. import db

def init_signals(app):
    """Initialize all signals within application context"""
    @user_registered.connect_via(app)
    def on_user_registered(sender, user, confirm_token, **extra):
        # Set user as unapproved by default
        user.is_approved = False
        db.session.commit()