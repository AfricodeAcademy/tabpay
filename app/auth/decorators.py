from functools import wraps
from flask import redirect, url_for, flash,current_app
from flask_login import current_user


def approval_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            current_app.logger.debug("User not authenticated. Redirecting to login.")
            return redirect(url_for('security.login'))
        
        if not current_user.is_approved:
            current_app.logger.debug(f"User {current_user.email} is not approved. Redirecting to pending approval.")
            flash('Your account is pending approval from an administrator.', 'warning')
            return redirect(url_for('auth.pending_approval'))
        
        current_app.logger.debug(f"User {current_user.email} is approved. Proceeding to requested page.")
        return f(*args, **kwargs)
    
    return decorated_function