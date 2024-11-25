from functools import wraps
from flask import redirect, url_for, flash, abort, current_app
from flask_login import current_user
from ..main.routes import get_umbrella_by_user


def approval_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_approved and not current_user.has_role('Administrator'):
            current_app.logger.info(f"User {current_user.email} is not approved. Redirecting to pending approval.")
            flash('Your account is pending approval from an administrator.', 'warning')
            return redirect(url_for('auth.pending_approval'))
        
        current_app.logger.debug(f"User {current_user.email} is approved with roles {current_user.roles}. Proceeding to requested page.")
        return f(*args, **kwargs)
    
    return decorated_function


def umbrella_required(f):
    """Decorator to ensure a user can only access data from their own umbrella."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('security.login'))

        # Get user's umbrella
        umbrella = get_umbrella_by_user(current_user.id)
        if not umbrella:
            flash('You need to create an umbrella before accessing this resource.', 'warning')
            return redirect(url_for('main.settings', active_tab='umbrella'))

        # If an umbrella_id is provided in kwargs, verify it matches the user's umbrella
        if 'umbrella_id' in kwargs and str(kwargs['umbrella_id']) != str(umbrella['id']):
            flash('You do not have permission to access this resource.', 'danger')
            abort(403)

        # If a block_id is provided, verify it belongs to the user's umbrella
        if 'block_id' in kwargs:
            from ..main.routes import get_blocks_by_umbrella
            blocks = get_blocks_by_umbrella()
            if not any(str(block['id']) == str(kwargs['block_id']) for block in blocks):
                flash('You do not have permission to access this block.', 'danger')
                abort(403)

        # Add the umbrella to kwargs for the decorated function to use
        kwargs['umbrella'] = umbrella
        return f(*args, **kwargs)

    return decorated_function