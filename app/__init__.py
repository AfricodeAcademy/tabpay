from flask import Flask,redirect, url_for, flash, render_template
from flask_restful import Api
from app import config
from flask_restful import Api
from app.api.api import Users,User,Communications,Communication,Payments,Payment,Blocks,Block,Umbrellas,Umbrella,Zones,Zone
from flask_security import  SQLAlchemyUserDatastore
from flask_security.utils import hash_password,verify_password,login_user,logout_user
from app.models.models import UserModel, Role
from app.extensions import security, db
from app.forms.auth import ExtendedRegisterForm

def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    # Initialize extensions
    db.init_app(app)
    
    # Setup Flask-Security
    user_datastore = SQLAlchemyUserDatastore(db, UserModel, Role)
    security.init_app(app, user_datastore, register_form=ExtendedRegisterForm)

    # Initialize Flask-RESTful API
    api = Api(app)
    api.add_resource(Users, '/api/v1/users/')
    api.add_resource(User, '/api/v1/users/<int:id>/')
    api.add_resource(Communications, '/api/v1/communications/')
    api.add_resource(Communication, '/api/v1/communications/<int:id>/')
    api.add_resource(Payments, '/api/v1/payments/')
    api.add_resource(Payment, '/api/v1/payments/<int:id>/')
    api.add_resource(Blocks, '/api/v1/blocks/')
    api.add_resource(Block, '/api/v1/blocks/<int:id>/')
    api.add_resource(Umbrellas, '/api/v1/umbrellas/')
    api.add_resource(Umbrella, '/api/v1/umbrellas/<int:id>/')
    api.add_resource(Zones, '/api/v1/zones/')
    api.add_resource(Zone, '/api/v1/zones/<int:id>/')


    @app.route('/',methods=['GET'])
    def home():
        return render_template('index.html',title='TabPay | Home')
    

    @app.route('/register', methods=['GET', 'POST'])
    def custom_register():
        form = ExtendedRegisterForm()  
        if form.validate_on_submit():
            print('Form validated and submitted successfully')
            try:
                user = UserModel.query.filter_by(email=form.email.data).first()
                if not user:
                    new_user = UserModel(
                        email=form.email.data,
                        password=hash_password(form.password.data),  
                        full_name=form.full_name.data, 
                        id_number=form.id_number.data 
                    )
                    db.session.add(new_user)
                    db.session.commit() 
                    flash("Registration successful! Please log in.", "success")
                    return redirect(url_for('security.login'))  
                else:
                    flash("Email already exists", "danger")
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred: {str(e)}", "danger")
        else:
            flash("Form validation failed", "danger")
            print(form.errors)

        return render_template('security/register_user.html',title='TabPay | Register' ,form=form)
    
    # @app.route('/login', methods=['GET', 'POST'])
    # def custom_login():
    #     form = LoginForm() 
    #     if form.validate_on_submit():
    #         user = User.query.filter_by(email=form.email.data).first()  
    #         if user and verify_password(form.password.data, user.password):  
    #             login_user(user) 
    #             flash("Login successful!", "success")
    #             return redirect(url_for('statistics'))
    #         else:
    #             flash("Invalid email or password", "danger")

    #     return render_template('security/login.html',title='TabPay | Login', form=form)

    
    @app.route('/statistics', methods=['GET'])
    def statistics():
        return render_template('statistics.html', title='Dashboard | Statistics')


    @app.route('/manage_contribution', methods=['GET'])
    def manage_contribution():
        return render_template('manage_contribution.html', title='Dashboard | Manage Contributions')


    @app.route('/host', methods=['GET'])
    def host():
        return render_template('host.html', title='Dashboard | Host')


    @app.route('/settings', methods=['GET'])
    def settings():
        return render_template('settings.html', title='Dashboard | Settings')


    @app.route('/block_reports', methods=['GET', 'POST'])
    def block_reports():
        return render_template('block_reports.html', title='Dashboard | Block Reports')


    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('home'))


    return app