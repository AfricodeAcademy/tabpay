from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_security import current_user
from flask import redirect, url_for, request, abort, flash, current_app, session
from flask_wtf.csrf import generate_csrf, validate_csrf
from functools import wraps

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
        
    def render(self, template, **kwargs):
        # Ensure CSRF token is available in all admin templates
        kwargs['csrf_token'] = generate_csrf()
        return super().render(template, **kwargs)

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

    def render(self, template, **kwargs):
        # Ensure CSRF token is available in all admin templates
        kwargs['csrf_token'] = generate_csrf()
        return super().render(template, **kwargs)

    def validate_form(self, form):
        if request.method == 'POST':
            token = request.form.get('csrf_token')
            current_app.logger.debug(f'CSRF token from form: {token}')
            if token:
                try:
                    current_app.logger.debug('Validating CSRF token...')
                    validate_csrf(token)
                    current_app.logger.debug('CSRF token validation successful')
                    flash('CSRF Validation passed', 'info')
                except Exception as e:
                    current_app.logger.error(f'CSRF Validation failed: {str(e)}')
                    flash(f'CSRF Validation failed. csrf_token in form:{token} ', 'error')
                    return False
            else:
                current_app.logger.debug('CSRF token is missing')
                flash('CSRF token is missing', 'error')
            return False
        return super().validate_form(form)

    def create_form(self, obj=None):
        form = super().create_form(obj)
        if hasattr(form, 'csrf_token'):
            form.csrf_token.data = generate_csrf()
        return form

    def edit_form(self, obj=None):
        form = super().edit_form(obj)
        if hasattr(form, 'csrf_token'):
            form.csrf_token.data = generate_csrf()
        return form

    def create_blueprint(self, admin):
        blueprint = super().create_blueprint(admin)
        
        # Wrap all POST endpoints with CSRF validation
        for endpoint, view_func in blueprint.view_functions.items():
            if endpoint.endswith('_post'):
                blueprint.view_functions[endpoint] = self._wrap_with_csrf(view_func)
                
        return blueprint
    
    def _wrap_with_csrf(self, f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method == 'POST':
                token = request.form.get('csrf_token')
                if not token:
                    token = request.headers.get('X-CSRFToken')
                if not token:
                    abort(400, description='CSRF token missing')
                try:
                    validate_csrf(token)
                except:
                    abort(400, description='CSRF validation failed')
            return f(*args, **kwargs)
        return decorated_function

class CustomAdmin(Admin):
    def __init__(self, *args, **kwargs):
        kwargs['template_mode'] = 'bootstrap4'
        kwargs['index_view'] = SecureBaseView()
        super().__init__(*args, **kwargs)