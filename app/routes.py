from flask import Blueprint,render_template

main = Blueprint('main', __name__)

#home route
@main.route('/')
def home():
  return render_template('index.html',title='TabPay | Home')

    
@main.route('/register')
def register():
    return render_template('register.html',title='TabPay | Register')

@main.route('/login')
def login():
    return render_template('login.html',title='TabPay | Login')
 
@main.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html',title='TabPay | Forgot Password')

@main.route('/dashboard_stats')
def dashboard_stats():
    return render_template('statistics.html', title='Dashboard | Statistics')

@main.route('/dashboard_settings')
def dashboard_settings():
    return render_template('settings.html', title='Dashboard | Settings')

@main.route('/manage_contribution')
def manage_contribution():
    return render_template('manage_contribution.html', title='Dashboard | Manage_contribution')

@main.route('/host')
def host():
    return render_template('host.html', title='Dashboard | host')

