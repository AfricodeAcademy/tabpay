from flask import Flask
from .base import CustomAdmin
from .views import UserAdminView, RoleAdminView

admin = CustomAdmin(name='TabPay Dashboard', template_mode='bootstrap4', base_template='admin/base.html') 

def init_admin(app: Flask, db):
    from app.main.models import UserModel, RoleModel
    
    # Initialize Admin
    admin.init_app(app)
    
    # Add views
    admin.add_view(UserAdminView(UserModel, db.session, name='Users'))
    admin.add_view(RoleAdminView(RoleModel, db.session, name='Roles'))
    
    return admin