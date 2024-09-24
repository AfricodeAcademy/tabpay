from flask import Blueprint, render_template, redirect, url_for,request
from flask_security import login_required, logout_user, roles_required
from flask_security.utils import hash_password
from ..api.api import user_datastore,db


# Blueprint for authentication routes
auth = Blueprint('auth', __name__)



@auth.route('/register', methods=['GET', 'POST'])
@roles_required('SuperUser')
def register_user():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        id_number = request.form.get('id_number')

        # Automatically assign the Umbrella_creator role
        umbrella_creator_role = user_datastore.find_or_create_role('Umbrella_creator')

        # Create the new user with the "Umbrella_creator" role
        hashed_password = hash_password(password)
        user_datastore.create_user(full_name=full_name, id_number=id_number, email=email, password=hashed_password, roles=[umbrella_creator_role])
        db.session.commit()

        return redirect(url_for('security.login'))

    return render_template('security/register_user.html')



























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





