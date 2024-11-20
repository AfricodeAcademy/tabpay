from flask import redirect, url_for, after_this_request
from flask_security import user_registered
from flask_login import user_logged_in
from ..utils import db
# import logging

def init_signals(app):
    """Initialize all signals within the application context."""

    @user_registered.connect_via(app)
    def on_user_registered(sender, user, confirm_token, **extra):
        """Handle post-registration actions."""
        # logging.debug(f"User {user.email} registered. Setting is_approved to False.")
        
        # Set additional user properties, if needed
        user.is_approved = False
        db.session.commit()

    @user_logged_in.connect_via(app)
    def on_user_logged_in(sender, user):
        """Handle role-based redirection after login."""
        
        @after_this_request
        def redirect_after_login(response):
            """Redirect based on user role."""
            if user.has_role('SuperUser'):
                return redirect(url_for('admin.index'))
            return redirect(url_for('main.statistics'))
        
        return None 
