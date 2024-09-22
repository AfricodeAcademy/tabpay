from app import create_app as app
from flask import render_template,redirect,url_for,request,flash
from flask_security import  roles_required, current_user
from flask_security.utils import hash_password
from app.extensions import db
from app.models.models import UserModel,UmbrellaModel, BlockModel,ZoneModel,user_datastore




# Profile route
@app.route('/settings/profile', methods=['GET', 'POST'])
@roles_required('Admin') 
def settings_profile():
    if request.method == 'POST':
        # Update user profile logic here
        full_name = request.form.get('fullName')
        id_number = request.form.get('id_number')
        new_password = request.form.get('newPassword')
        confirm_password = request.form.get('confirmPassword')

        # Ensure passwords match and apply other validations
        if new_password == confirm_password:
            current_user.full_name = full_name
            current_user.id_number = id_number
            if new_password:
                current_user.password = hash_password(new_password)
            db.session.commit()
            flash('Profile updated successfully!')
        else:
            flash('Passwords do not match!')

        return redirect(url_for('settings_profile'))
    return render_template('settings/profile.html')

