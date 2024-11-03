from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def approval_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('security.login'))
        
        if not current_user.is_approved:
            flash('Your account is pending approval from an administrator.', 'warning')
            return redirect(url_for('auth.pending_approval'))
            
        return f(*args, **kwargs)
    return decorated_function