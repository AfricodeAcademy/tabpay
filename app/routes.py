from flask import Blueprint,render_template

main = Blueprint('main', __name__)

#home route
@main.route('/')
def home():
    return render_template('index.html')

@main.route('/create_new_account')
def create_new_account():
    return render_template('create_new_account.html')
