from .base import SecureModelView
from flask_security import current_user
from flask import flash, redirect, url_for, abort
from flask_admin.actions import action

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