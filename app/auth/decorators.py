from functools import wraps
from flask import redirect, url_for, flash, abort, current_app, request
from flask_login import current_user
from ..utils.umbrella import get_umbrella_by_user, get_blocks_by_umbrella


def approval_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_approved and not current_user.has_role('Administrator'):
            # current_app.logger.debug(f"User {current_user.email} is not approved. Redirecting to pending approval.")
            flash('Your account is pending approval from an administrator.', 'warning')
            return redirect(url_for('auth.pending_approval'))
        
        # current_app.logger.debug(f"User {current_user.email} is approved.{current_user.roles} Proceeding to requested page.")
        return f(*args, **kwargs)
    
    return decorated_function


def umbrella_required(f):
    """Decorator to ensure a user can only access data from their own umbrella."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        
        # Log request details
        logger.info(f"[UMBRELLA_CHECK] Endpoint: {request.endpoint}, Method: {request.method}, Path: {request.path}")
        logger.info(f"[UMBRELLA_CHECK] User: {current_user.id if current_user else 'Not authenticated'}")
        
        # Check if user is logged in
        if not current_user.is_authenticated:
            logger.warning("[UMBRELLA_CHECK] User not authenticated, redirecting to login")
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('security.login'))

        # Get user's umbrella
        umbrella = get_umbrella_by_user(current_user.id)
        logger.info(f"[UMBRELLA_CHECK] User umbrella: {umbrella}")
        
        # Prevent redirect loops by checking current endpoint and request method
        current_endpoint = request.endpoint
        is_settings_page = current_endpoint == 'main.settings'
        is_get_request = request.method == 'GET'
        
        logger.info(f"[UMBRELLA_CHECK] Is settings page: {is_settings_page}")
        logger.info(f"[UMBRELLA_CHECK] Is GET request: {is_get_request}")
        
        # Only allow access to settings page without umbrella if it's a GET request
        if not umbrella and not (is_settings_page and is_get_request):
            logger.warning("[UMBRELLA_CHECK] No umbrella found, redirecting to settings")
            flash('You need to create an umbrella before accessing this resource.', 'warning')
            return redirect(url_for('main.settings', active_tab='umbrella'))

        # If an umbrella_id is provided in kwargs, verify it matches the user's umbrella
        if umbrella and 'umbrella_id' in kwargs:
            logger.info(f"[UMBRELLA_CHECK] Checking umbrella_id match: {kwargs['umbrella_id']} vs {umbrella['id']}")
            if str(kwargs['umbrella_id']) != str(umbrella['id']):
                logger.error("[UMBRELLA_CHECK] Umbrella ID mismatch")
                flash('You do not have permission to access this resource.', 'danger')
                abort(403)

        # If a block_id is provided, verify it belongs to the user's umbrella
        if umbrella and 'block_id' in kwargs:
            logger.info(f"[UMBRELLA_CHECK] Checking block permission for block_id: {kwargs['block_id']}")
            blocks = get_blocks_by_umbrella(show_flash_messages=False)
            if not any(str(block['id']) == str(kwargs['block_id']) for block in blocks):
                logger.error("[UMBRELLA_CHECK] Block permission denied")
                flash('You do not have permission to access this block.', 'danger')
                abort(403)

        # Add the umbrella to kwargs for the decorated function to use
        if umbrella:
            kwargs['umbrella'] = umbrella
            
        logger.info("[UMBRELLA_CHECK] Access granted, proceeding to view")
        return f(*args, **kwargs)

    return decorated_function