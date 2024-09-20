from flask import url_for,redirect
from ..extensions import auth_blueprint



@auth_blueprint.route('/logout')
def logout():
    return redirect(url_for('home'))
