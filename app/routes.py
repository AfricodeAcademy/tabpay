from flask import Blueprint,render_template

main = Blueprint('main', __name__)

#home route
@main.route('/')
def home():
    return render_template('index.html')

@main.route('/forgot')
def forgot():
    return render_template('forgot_password.html')


