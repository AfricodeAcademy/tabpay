from flask import Blueprint,render_template

main = Blueprint('main', __name__)

#home route
@main.route('/')
def home():
    return render_template('index.html',title='TabPay | Home')

@main.route('/dashboard_stats')
def dashboard_stats():
    return render_template('template-5.html', title='Dashboard | Statistics')

@main.route('/dashboard_settings')
def dashboard_settings():
    return render_template('template-6.html', title='Dashboard | Settings')