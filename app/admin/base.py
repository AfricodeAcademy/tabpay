from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_security import current_user
from flask import redirect, url_for, request, abort, flash, current_app, session
from flask_wtf.csrf import generate_csrf, validate_csrf

class SecureBaseView(AdminIndexView):
    def is_accessible(self):
        return (current_user.is_active and 
                current_user.is_authenticated and 
                (current_user.has_role('SuperUser') or 
                 current_user.has_role('Administrator')))
    
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            if current_user.is_authenticated:
                abort(403)
            return redirect(url_for('security.login', next=request.url))
        
    def get_extra_args(self):
        args = super().get_extra_args()
        # Generate a fresh CSRF token and ensure it's in the session
        token = generate_csrf()
        if 'csrf_token' not in session:
            session['csrf_token'] = token
        args['csrf_token'] = token
        return args

class SecureModelView(ModelView):
    form_base_class = SecureForm
    
    def is_accessible(self):
        return (current_user.is_active and 
                current_user.is_authenticated and 
                (current_user.has_role('SuperUser') or 
                 current_user.has_role('Administrator')))

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            if current_user.is_authenticated:
                abort(403)
            return redirect(url_for('security.login', next=request.url))

    def get_extra_args(self):
        args = super().get_extra_args()
        # Generate a fresh CSRF token and ensure it's in the session
        token = generate_csrf()
        if 'csrf_token' not in session:
            session['csrf_token'] = token
        args['csrf_token'] = token
        return args
    
    def is_action_allowed(self, name):
        # Skip CSRF validation for GET requests
        if request.method == 'GET':
            return super().is_action_allowed(name)
            
        # Get the token from either form data or headers
        csrf_token = request.form.get('csrf_token')
        if not csrf_token:
            csrf_token = request.headers.get('X-CSRFToken')
            
        if not csrf_token:
            error_msg = 'CSRF token missing. Token not found in form data or X-CSRFToken header.'
            current_app.logger.error(error_msg)
            flash(error_msg, 'error')
            return False
            
        try:
            # Ensure session is initialized
            if 'csrf_token' not in session:
                session['csrf_token'] = generate_csrf()
                
            # Use Flask-WTF's validate_csrf function
            validate_csrf(csrf_token)
            return super().is_action_allowed(name)
        except Exception as e:
            error_details = f"CSRF validation failed: {str(e)}. "
            error_details += f"Request method: {request.method}. "
            error_details += f"Token length: {len(csrf_token)}. "
            error_details += f"Session exists: {bool(session)}. "
            if session:
                error_details += f"Session csrf_token exists: {'csrf_token' in session}. "
            
            current_app.logger.error(error_details)
            flash(error_details, 'error')
            return False

    def create_form(self, obj=None):
        form = super().create_form(obj)
        form.csrf_token.data = generate_csrf()
        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        form.csrf_token.data = generate_csrf()
        return form

    def get_create_form(self):
        form = super().get_create_form()
        return form

    def get_edit_form(self):
        form = super().get_edit_form()
        return form

    def get_action_form(self):
        form = super().get_action_form()
        return form

class CustomAdmin(Admin):
    def __init__(self, *args, **kwargs):
        kwargs['template_mode'] = 'bootstrap4'
        kwargs['index_view'] = SecureBaseView()
        super(CustomAdmin, self).__init__(*args, **kwargs)