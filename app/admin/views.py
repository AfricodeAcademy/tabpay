from flask import flash, redirect, url_for, abort, request, current_app, session
from flask_security import current_user
from flask_admin.actions import action
from .base import SecureModelView
from flask_wtf.csrf import generate_csrf, validate_csrf

class SecureModelView(SecureModelView):
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

class UserAdminView(SecureModelView):
    column_exclude_list = ['password']
    column_searchable_list = ['email', 'full_name', 'phone_number', 'id_number']
    column_filters = ['active', 'roles', 'is_approved']
    form_excluded_columns = ['password', 'approval_date', 'approved_by']
    can_create = True
    can_edit = True
    can_delete = False
    
    column_list = ['email', 'full_name', 'active', 'is_approved', 'approval_date', 'approved_by']
    
    @action('approve', 'Approve Users', 'Are you sure you want to approve the selected users?')
    def action_approve(self, ids):
        try:
            query = self.model.query.filter(self.model.id.in_(ids))
            count = 0
            for user in query.all():
                if not user.is_approved:
                    user.approve(current_user)
                    count += 1
            
            flash(f'{count} users were successfully approved.')
            return redirect(url_for('.index_view'))
            
        except Exception as ex:
            flash(f'Failed to approve users. {str(ex)}', 'error')
            return redirect(url_for('.index_view'))
    
    @action('unapprove', 'Unapprove Users', 'Are you sure you want to unapprove the selected users?')
    def action_unapprove(self, ids):
        try:
            query = self.model.query.filter(self.model.id.in_(ids))
            count = 0
            for user in query.all():
                if user.is_approved:
                    user.unapprove()
                    count += 1
            
            flash(f'{count} users were successfully unapproved.')
            return redirect(url_for('.index_view'))
            
        except Exception as ex:
            flash(f'Failed to unapprove users. {str(ex)}', 'error')
            return redirect(url_for('.index_view'))
    
    def on_model_change(self, form, model, is_created):
        if not current_user.has_role('SuperUser'):
            if 'SuperUser' in [role.name for role in model.roles]:
                abort(403)
        return super().on_model_change(form, model, is_created)

class RoleAdminView(SecureModelView):
    column_list = ['name', 'description']
    column_searchable_list = ['name', 'description']
    can_create = False
    can_delete = False
    can_edit = True