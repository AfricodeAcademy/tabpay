from flask import Flask
from .base import CustomAdmin
from .views import UserAdminView, RoleAdminView

admin = CustomAdmin(name='TabPay Admin')

def init_admin(app: Flask, db):
    from app.main.models import UserModel, RoleModel
    
    # Configure CSRF protection
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600
    app.config['WTF_CSRF_SECRET_KEY'] = app.config['SECRET_KEY']
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    
    # Initialize Admin
    admin.init_app(app)
    
    # Add views
    admin.add_view(UserAdminView(UserModel, db.session, name='Users'))
    admin.add_view(RoleAdminView(RoleModel, db.session, name='Roles'))
    
    return admin