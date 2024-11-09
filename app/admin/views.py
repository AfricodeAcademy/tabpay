from .base import SecureModelView
from flask_security import current_user
from flask import flash, redirect, url_for, abort, request, current_app
from flask_wtf.csrf import validate_csrf
from flask_admin.actions import action
import traceback

class UserAdminView(SecureModelView):
    column_exclude_list = ['password']
    column_searchable_list = ['email', 'full_name', 'phone_number', 'id_number']
    column_filters = ['active', 'roles', 'is_approved']
    form_excluded_columns = ['password', 'approval_date', 'approved_by']
    form_columns = ['full_name','email', 'phone_number', 'id_number', 'active', 'roles', 'is_approved']
    can_create = True
    can_edit = True
    can_delete = False
    
    column_list = ['email', 'full_name', 'active', 'is_approved', 'approval_date', 'approved_by']
    
    @property
    def can_approve(self):
        if not current_user.is_authenticated:
            return False
        
        # Check if the user has a specific role that allows approval
        if current_user.has_role('SuperUser') or current_user.has_role('Approver'):
            return True
        
        # Check if the user has a specific permission
        if hasattr(current_user, 'has_permission'):
            return current_user.has_permission('approve_users')
        
        # If you're using a simple boolean flag on the user model
        if hasattr(current_user, 'can_approve_users'):
            return current_user.can_approve_users
        
        # Default to False if none of the above conditions are met
        return False

    @action('approve', 'Approve Users', 'Are you sure you want to approve the selected users?')
    def action_approve(self, ids):
        try:
            current_app.logger.debug(f"action_approve called with ids: {ids}")
            # Retrieve the CSRF token from the form data
            csrf_token = request.form.get('csrf_token')
            current_app.logger.debug(f"CSRF token retrieved: {csrf_token}")

            if csrf_token:
                try:
                    validate_csrf(csrf_token)
                    current_app.logger.debug("CSRF token validated successfully")
                except Exception as csrf_ex:
                    current_app.logger.error(f"CSRF validation failed: {str(csrf_ex)}")
                    flash('CSRF token validation failed', 'error')
                    return redirect(url_for('.index_view'))

            else:
                current_app.logger.error(f"CSRF validation failed: {str(csrf_ex)}")
                flash('CSRF token missing', 'error')
                return redirect(url_for('.index_view'))
            current_app.logger.debug(f"Attempting to approve users with ids: {ids}")
            query = self.model.query.filter(self.model.id.in_(ids))
            count = 0
            for user in query.all():
                current_app.logger.debug(f"Processing user {user.id}: current approval status = {user.is_approved}")
                if not user.is_approved:
                    user.approve(current_user)
                    count += 1
                    current_app.logger.debug(f"User {user.id} approved")
                else:
                    current_app.logger.debug(f"User {user.id} already approved, skipping")
                    
            current_app.logger.debug("Committing changes to database")    
            current_app.extensions['sqlalchemy'].db.session.commit()
            current_app.logger.debug(f"Approved {count} users")
            flash(f'{count} users were successfully approved.')
            return redirect(url_for('.index_view'))
            
        except Exception as ex:
            current_app.logger.error(f"Error in action_approve: {str(ex)}")
            current_app.logger.error(traceback.format_exc())
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