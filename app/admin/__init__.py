from flask import Flask
from .base import CustomAdmin, SecureModelView
from .views import UserAdminView, RoleAdminView, UmbrellaAdminView



def init_admin(app: Flask, db):
    admin = CustomAdmin(app, name='TabPay ', template_mode='bootstrap4', base_template='admin/my_base.html') 
    
    from app.main.models import UserModel, RoleModel,UmbrellaModel
    
    
    # Add views
    admin.add_view(UserAdminView(UserModel, db.session, name='Users', menu_icon_type="fa", menu_icon_value='fa-users'))
    admin.add_view(RoleAdminView(RoleModel, db.session, name='Roles', menu_icon_type="fa", menu_icon_value='fa-user-shield'))
    admin.add_view(UmbrellaAdminView(UmbrellaModel, db.session, name='Umbrellas', menu_icon_type="fa", menu_icon_value='fa-umbrella'))


    
    return admin