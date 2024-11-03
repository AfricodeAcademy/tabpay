from flask_admin import Admin, expose
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from flask import redirect, url_for, request, abort, flash
from flask_admin.form import SecureForm
from flask_admin.actions import action
from datetime import datetime


admin = Admin(name='TabPay Admin', template_mode='bootstrap4')
class SecureModelView(ModelView):
    form_base_class = SecureForm  # Adds CSRF protection to forms
    
    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('SuperUser'))
    
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            if current_user.is_authenticated:
                abort(403)  # Permission denied
            return redirect(url_for('security.login', next=request.url))
class UserAdminView(SecureModelView):
    column_exclude_list = ['password']
    column_searchable_list = ['email', 'full_name', 'phone_number', 'id_number']
    column_filters = ['active', 'roles', 'is_approved']
    form_excluded_columns = ['password', 'approval_date', 'approved_by']
    can_create = True
    can_edit = True
    can_delete = False  # For safety, disable user deletion
    
    # Add approval status to list view
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
        except Exception as ex:
            flash(f'Failed to approve users. {str(ex)}', 'error')
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
        except Exception as ex:
            flash(f'Failed to unapprove users. {str(ex)}', 'error')
    
    def on_model_change(self, form, model, is_created):
        # Prevent modification of Admin users by non-Admin users
        if not current_user.has_role('SuperUser'):
            if 'SuperUser' in [role.name for role in model.roles]:
                abort(403)
        return super().on_model_change(form, model, is_created)
class RoleAdminView(SecureModelView):
    column_list = ['name', 'description']
    column_searchable_list = ['name', 'description']
    can_create = False  # Prevent creation of new roles through admin
    can_delete = False  # Prevent deletion of roles
    can_edit = True    # Allow editing role descriptions
def init_admin(app, db):
    from app.main.models import UserModel, RoleModel
    
    # Initialize Admin
    admin.init_app(app)
    
    # Add views
    admin.add_view(UserAdminView(UserModel, db.session, name='Users'))
    admin.add_view(RoleAdminView(RoleModel, db.session, name='Roles'))
    
    return admin