from flask import Blueprint,render_template

main = Blueprint('main', __name__)

#home route
@main.route('/')
def home():
   return render_template('index.html',title='TabPay | Home')


@main.route('/create_new_account')
def create_new_account():
    return render_template('create_new_account.html')

   

@main.route('/dashboard')
def dashboard():
    return render_template('template-5.html', title='Dashboard')

@main.route('/management')
def management():
    return render_template('management.html', title='Management')

