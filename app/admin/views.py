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
    action_disallowed_list = []
    can_export = True
    details_modal = True
    edit_modal = True
    create_modal = True
    can_view_details = True
    column_details_list = ('full_name', 'email','phone_number', 'id_number','is_approved', 'approval_date', 'approved_by','roles')
    column_list = ['email', 'full_name', 'phone_number', 'id_number', 'roles', 'active', 'is_approved', 'approval_date', 'approved_by']

    @expose('/action/', methods=['POST'])
    def action_view(self):
        csrf_token = request.form.get('csrf_token')
        if not csrf_token:
            flash('CSRF token missing', 'error')
            return redirect(url_for('.index_view'))

        try:
            validate_csrf(csrf_token)
        except Exception as csrf_ex:
            flash('CSRF validation failed', 'error')
            return redirect(url_for('.index_view'))

        return self.handle_action()
 
    @property
    def can_approve(self):
        if not current_user.is_authenticated:
            return False
        if current_user.has_role('SuperUser') or current_user.has_role('Approver'):
            return True
        if hasattr(current_user, 'has_permission'):
            return current_user.has_permission('approve_users')
        if hasattr(current_user, 'can_approve_users'):
            return current_user.can_approve_users
        return False
    
    def handle_action(self):
        # logger = current_app.logger
        # logger.debug("handle_action called")

        try:
            action = request.form.get('action')
            ids = request.form.getlist('rowid')
            
            # logger.debug(f"Action: {action}, IDs: {ids}")

            if action == 'approve':
                return self.action_approve(ids)
            elif action == 'unapprove':
                return self.action_unapprove(ids)
            
            return super().handle_action(action, ids)

        except Exception as e:
            # logger.error(f"Error in handle_action: {str(e)}")
            # logger.error(traceback.format_exc())
            flash(f'Action failed: {str(e)}', 'error')
            return redirect(url_for('.index_view'))


    @action('approve', 'Approve Users', 'Are you sure you want to approve the selected users?')
    def action_approve(self, ids):
        # logger = current_app.logger
        try:
            # logger.debug(f"Attempting to approve users with ids: {ids}")
            query = self.model.query.filter(self.model.id.in_(ids))
            count = 0
            
            for user in query.all():
                if not user.is_approved:
                    user.approve(current_user)
                    count += 1
                    # logger.debug(f"User {user.id} approved")
                    
            self.session.commit()
            flash(f'{user.full_name} successfully approved.')
            
        except Exception as ex:
            # logger.error(f"Error in action_approve: {str(ex)}")
            # logger.error(traceback.format_exc())
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
            flash(f'{user.full_name} successfully unapproved.')
            
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
    @expose('/action/', methods=['POST'])
    def action_view(self):
        csrf_token = request.form.get('csrf_token')
        if not csrf_token:
            flash('CSRF token missing', 'error')
            return redirect(url_for('.index_view'))

        try:
            validate_csrf(csrf_token)
        except Exception as csrf_ex:
            flash('CSRF validation failed', 'error')
            return redirect(url_for('.index_view'))

        return self.handle_action()
    


class UmbrellaAdminView(SecureModelView):
    # Customize the list view, including filters and columns shown
    column_list = ['name','location','blocks', 'created_by']
    column_searchable_list = ['name', 'created_by','location']
    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True

    # Form configuration for creating or editing an umbrella
    form_columns = ['name', 'location']

    @expose('/action/', methods=['POST'])
    def action_view(self):
        # CSRF protection for actions
        csrf_token = request.form.get('csrf_token')
        if not csrf_token:
            flash('CSRF token missing', 'error')
            return redirect(url_for('.index_view'))

        try:
            validate_csrf(csrf_token)
        except Exception as csrf_ex:
            flash('CSRF validation failed', 'error')
            return redirect(url_for('.index_view'))

        return self.handle_action()

    def handle_action(self):
        # logger = current_app.logger
        # logger.debug("handle_action called")

        try:
            action = request.form.get('action')
            ids = request.form.getlist('rowid')
            
            # logger.debug(f"Action: {action}, IDs: {ids}")

            if action == 'approve':
                return self.action_approve(ids)
            elif action == 'unapprove':
                return self.action_unapprove(ids)
            
            return super().handle_action(action, ids)

        except Exception as e:
            # logger.error(f"Error in handle_action: {str(e)}")
            # logger.error(traceback.format_exc())
            flash(f'Action failed: {str(e)}', 'error')
            return redirect(url_for('.index_view'))

    @action('approve', 'Approve Umbrellas', 'Are you sure you want to approve the selected umbrellas?')
    def action_approve(self, ids):
        # logger = current_app.logger
        try:
            # logger.debug(f"Attempting to approve umbrellas with ids: {ids}")
            query = self.model.query.filter(self.model.id.in_(ids))
            count = 0
            
            for umbrella in query.all():
                if not umbrella.is_approved:
                    umbrella.is_approved = True
                    count += 1
                    # logger.debug(f"Umbrella {umbrella.id} approved")
                    
            self.session.commit()
            flash(f'{count} umbrellas were successfully approved.')
            
        except Exception as ex:
            # logger.error(f"Error in action_approve: {str(ex)}")
            # logger.error(traceback.format_exc())
            flash(f'Failed to approve umbrellas: {str(ex)}', 'error')
            
        return redirect(url_for('.index_view'))

    @action('unapprove', 'Unapprove Umbrellas', 'Are you sure you want to unapprove the selected umbrellas?')
    def action_unapprove(self, ids):
        try:
            query = self.model.query.filter(self.model.id.in_(ids))
            count = 0
            for umbrella in query.all():
                if umbrella.is_approved:
                    umbrella.is_approved = False
                    count += 1
            
            self.session.commit()
            flash(f'{count} umbrellas were successfully unapproved.')
            
        except Exception as ex:
            flash(f'Failed to unapprove umbrellas: {str(ex)}', 'error')
            
        return redirect(url_for('.index_view'))

    def on_model_change(self, form, model, is_created):
        if not current_user.has_role('SuperUser'):
            abort(403)
        return super().on_model_change(form, model, is_created)
