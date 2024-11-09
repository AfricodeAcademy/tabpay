from .base import SecureModelView
from flask_security import current_user
from flask import flash, redirect, url_for, abort, request, current_app
from flask_wtf.csrf import validate_csrf
from flask_admin.actions import action
import traceback
from flask_admin import expose

class UserAdminView(SecureModelView):
    list_template = 'admin/model/mylist.html'
    column_exclude_list = ['password']
    column_searchable_list = ['email', 'full_name', 'phone_number', 'id_number']
    column_filters = ['active', 'roles', 'is_approved']
    form_excluded_columns = ['password', 'approval_date', 'approved_by']
    form_columns = ['full_name','email', 'phone_number', 'id_number', 'active', 'roles', 'is_approved']
    can_create = True
    can_edit = True
    can_delete = False
    action_disallowed_list = []  # Make sure no actions are disallowed
    can_export = True  # Enable export functionality
    can_view_details = True  # Enable detail view
    
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
    
    def handle_action(self, action, ids):
        logger = current_app.logger
        logger.debug(f"handle_action called with action: {action}, ids: {ids}")

        try:
            # Validate CSRF token
            csrf_token = request.form.get('csrf_token')
            if not csrf_token:
                flash('CSRF token missing', 'error')
                return redirect(url_for('.index_view'))

            try:
                validate_csrf(csrf_token)
            except Exception as csrf_ex:
                flash('CSRF validation failed', 'error')
                return redirect(url_for('.index_view'))

            # Handle specific actions
            if action == 'approve':
                return self.action_approve(ids)
            elif action == 'unapprove':
                return self.action_unapprove(ids)
            
            return super().handle_action(action, ids)

        except Exception as e:
            logger.error(f"Error in handle_action: {str(e)}")
            logger.error(traceback.format_exc())
            flash(f'Action failed: {str(e)}', 'error')
            return redirect(url_for('.index_view'))


    @action('approve', 'Approve Users', 'Are you sure you want to approve the selected users?')
    def action_approve(self, ids):
        logger = current_app.logger
        try:
            logger.debug(f"Attempting to approve users with ids: {ids}")
            query = self.model.query.filter(self.model.id.in_(ids))
            count = 0
            
            for user in query.all():
                if not user.is_approved:
                    user.approve(current_user)
                    count += 1
                    logger.debug(f"User {user.id} approved")
                    
            self.session.commit()
            flash(f'{count} users were successfully approved.')
            
        except Exception as ex:
            logger.error(f"Error in action_approve: {str(ex)}")
            logger.error(traceback.format_exc())
            flash(f'Failed to approve users: {str(ex)}', 'error')
            
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
            
            self.session.commit()
            flash(f'{count} users were successfully unapproved.')
            
        except Exception as ex:
            flash(f'Failed to unapprove users: {str(ex)}', 'error')
            
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