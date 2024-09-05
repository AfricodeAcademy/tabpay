from flask import Blueprint,render_template

main = Blueprint('main', __name__)

#home route
@main.route('/')
def home():
    return render_template('index.html',title='TabPay | Home')

@main.route('/dashboard')
def dashboard():
    return render_template('template-5.html', title='Dashboard')