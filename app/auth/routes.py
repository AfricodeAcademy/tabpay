from flask import render_template, redirect, url_for
from flask_login import current_user
from . import auth

@auth.route('/pending-approval')
def pending_approval():
    if current_user.is_approved:
        return redirect(url_for('main.statistics'))
    return render_template('pending_approval.html')
