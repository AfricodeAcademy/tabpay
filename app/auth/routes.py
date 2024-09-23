from flask import Blueprint, render_template, redirect, url_for
from flask_security import login_required, logout_user
from app.auth.forms import ExtendedRegisterForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Implement login logic
    pass

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = ExtendedRegisterForm()
    if form.validate_on_submit():
        # Implement registration logic
        pass
    return render_template('auth/register.html', form=form)






























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





