<<<<<<< HEAD
<<<<<<< HEAD
# from flask import Blueprint, render_template, redirect, url_for,request
# from flask_security import login_required, logout_user, roles_required
# from flask_security.utils import hash_password
# from ..api.api import user_datastore,db


# # Blueprint for authentication routes
# auth = Blueprint('auth', __name__)



# from app.auth.forms import ExtendedConfirmRegisterForm

# @auth.route('/register', methods=['GET', 'POST'])
# @roles_required('Administrator')  
# def register_user():
#     form = ExtendedConfirmRegisterForm()

#     if form.validate_on_submit(): 
#         full_name = form.full_name.data
#         email = form.email.data
#         password = form.password.data
#         id_number = form.id_number.data

#         # Automatically assign the Umbrella_creator role
#         umbrella_creator_role = user_datastore.find_or_create_role('Umbrella_creator')

#         # Create the new user with the "Umbrella_creator" role
#         hashed_password = hash_password(password)
#         user_datastore.create_user(full_name=full_name, id_number=id_number, email=email, password=hashed_password, roles=[umbrella_creator_role])
#         db.session.commit()

#         return redirect(url_for('security.login'))

#     return render_template('security/register_user.html', form=form)



























# @auth.route('/register', methods=['GET', 'POST'])
# def custom_register():
#     form = ExtendedRegisterForm()  
#     if form.validate_on_submit():
#         print('Form validated ')
#         try:
#             user = UserModel.query.filter_by(email=form.email.data).first()
#             if not user:
#                 new_user = UserModel(
#                     email=form.email.data,
#                     password=hash_password(form.password.data),  
#                     full_name=form.full_name.data, 
#                     id_number=form.id_number.data 
#                 )
#                 db.session.add(new_user)
#                 db.session.commit() 
#                 flash("Registration successful! Please log in.", "success")
#                 return redirect(url_for('security.login'))  
#             else:
#                 flash("Email already exists", "danger")
#         except Exception as e:
#             db.session.rollback()
#             flash(f"An error occurred: {str(e)}", "danger")
#     else:
#         flash("Form validation failed", "danger")
#         print(form.errors)

#     return render_template('security/register_user.html',title='TabPay | Register' ,form=form)




=======
from flask import render_template, redirect, url_for
from flask_login import current_user
from . import auth
>>>>>>> admin-management
=======
from flask import render_template, redirect, url_for
from flask_login import current_user
from . import auth
>>>>>>> 2f07c12ef03e8370ce2bbb4219f4fe3c1ef0269b

@auth.route('/pending-approval')
def pending_approval():
    if current_user.is_approved:
        return redirect(url_for('main.statistics'))
    return render_template('pending_approval.html')
