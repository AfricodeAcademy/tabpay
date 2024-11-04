from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_security import current_user
from flask import redirect, url_for, request, abort
from flask_admin.form import SecureForm

class SecureBaseView(AdminIndexView):
    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('SuperUser'))
    
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            if current_user.is_authenticated:
                abort(403)
            return redirect(url_for('security.login', next=request.url))

class SecureModelView(ModelView):
    form_base_class = SecureForm
    
    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('SuperUser'))
    
    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            if current_user.is_authenticated:
                abort(403)
            return redirect(url_for('security.login', next=request.url))
    
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