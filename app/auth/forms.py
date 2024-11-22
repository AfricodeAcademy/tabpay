from flask_security.forms import ConfirmRegisterForm, LoginForm, RegisterForm
from wtforms import StringField, IntegerField, EmailField, PasswordField
from wtforms.validators import DataRequired, Length, ValidationError, EqualTo
from ..api.api import UserModel
from flask import request

class ExtendedRegisterForm(RegisterForm):
    full_name = StringField('Please enter your Full Names', 
                            validators=[DataRequired(message="Full name is required!"), Length(min=4, max=20)],
                            render_kw={'placeholder': 'Jiara Martins'})
    email = EmailField('Please enter your Email', 
                       validators=[DataRequired(message="Email is required!")],
                       render_kw={'placeholder': 'hello@reallygreatsite.com'})
    password = PasswordField('Please enter Password', 
                             validators=[DataRequired(message="Password is required!")], 
                             render_kw={'placeholder': '********'})
    confirm_password = PasswordField('Please confirm your Password', 
                                     validators=[DataRequired(message="Please confirm your password!"),
                                                 EqualTo('password', message="Passwords must match!")],
                                     render_kw={'placeholder': '********'})

    def validate_email(self, field):
        """Check if the email already exists in the database."""
        if UserModel.query.filter_by(email=field.data).first():
            raise ValidationError("This email is already registered. Please use a different email.")


class ExtendedConfirmRegisterForm(ConfirmRegisterForm):
    full_name = StringField('Please enter your Full Names', 
                            validators=[DataRequired(message="Full name is required!"), Length(min=4, max=20)],
                            render_kw={'placeholder': 'Jiara Martins'})
    email = EmailField('Please enter your Email', 
                       validators=[DataRequired(message="Email is required!")],
                       render_kw={'placeholder': 'hello@reallygreatsite.com'})
    password = PasswordField('Please enter Password', 
                             validators=[DataRequired(message="Password is required!")], 
                             render_kw={'placeholder': '********'})
    confirm_password = PasswordField('Please confirm your Password', 
                                     validators=[DataRequired(message="Please confirm your password!"),
                                                 EqualTo('password', message="Passwords must match!")],
                                     render_kw={'placeholder': '********'})

    def validate_email(self, field):
        """Check if the email already exists in the database."""
        if UserModel.query.filter_by(email=field.data).first():
            raise ValidationError("This email is already registered. Please use a different email.")

  


class ExtendedLoginForm(LoginForm):
    email = EmailField('Please enter your Email', 
                      validators=[DataRequired(message="Email is required!")],
                      render_kw={'placeholder':'hello@reallygreatsite.com'})
    password = PasswordField('Please enter Password', 
                           validators=[DataRequired(message="Password is required!")], 
                           render_kw={'placeholder':'******'})
    
    def __init__(self, *args, **kwargs):
        super(ExtendedLoginForm, self).__init__(*args, **kwargs)
        self.next.data = request.args.get('next', '')



# class ExtendedSendConfirmationForm(SendConfirmationForm):
#     email = EmailField('Please enter your Email', validators=[DataRequired()],render_kw={'placeholder':'hello@reallygreatsite.com'})
