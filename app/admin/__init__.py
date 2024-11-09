from flask import Flask
from .base import CustomAdmin, SecureModelView
from .views import UserAdminView, RoleAdminView



def init_admin(app: Flask, db):
    admin = CustomAdmin(app, name='TabPay Dashboard', template_mode='bootstrap4', base_template='admin/my_base.html') 
    
    from app.main.models import UserModel, RoleModel
    
    
    # Add views
    admin.add_view(UserAdminView(UserModel, db.session, name='Users'))
    admin.add_view(RoleAdminView(RoleModel, db.session, name='Roles'))
    
    return admin