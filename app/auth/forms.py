from flask_security.forms import ConfirmRegisterForm,LoginForm,RegisterForm
from wtforms import StringField,IntegerField,EmailField, PasswordField
from wtforms.validators import DataRequired, Length,ValidationError
from ..api.api import UserModel

class ExtendedRegisterForm(RegisterForm):
    full_name = StringField('Please enter your Full Names',  validators=[DataRequired(message="Full name is required!"), Length(min=4, max=20)],render_kw={'placeholder':'Jiara Martins'})
    id_number = IntegerField('ID No:', validators=[DataRequired(message="ID Number is required!")],render_kw={'placeholder':'xxxxxxxx'})
    email = EmailField('Please enter your Email', validators=[DataRequired(message="Email is required!")],render_kw={'placeholder':'hello@reallygreatsite.com'})
    password = PasswordField('Please enter Password', validators=[DataRequired(message="Password is required!")], render_kw={'placeholder':'********'})

    def validate_email(self, field):
        """Check if the email already exists in the database."""
        if UserModel.query.filter_by(email=field.data).first():
            raise ValidationError("This email is already registered. Please use a different email.")
    
    def validate_id_number(self, field):
        """Check if the ID number already exists in the database."""
        if UserModel.query.filter_by(id_number=field.data).first():
            raise ValidationError("This ID number is already registered. Please use a different ID number.")


class ExtendedConfirmRegisterForm(ConfirmRegisterForm):
    full_name = StringField('Please enter your Full Names',  validators=[DataRequired(message="Full name is required!"), Length(min=4, max=20)],render_kw={'placeholder':'Jiara Martins'})
    id_number = IntegerField('ID No:', validators=[DataRequired(message="ID Number is required!")],render_kw={'placeholder':'xxxxxxxx'})
    email = EmailField('Please enter your Email', validators=[DataRequired(message="Email is required!")],render_kw={'placeholder':'hello@reallygreatsite.com'})
    password = PasswordField('Please enter Password', validators=[DataRequired(message="Password is required!")], render_kw={'placeholder':'********'})

    def validate_email(self, field):
        """Check if the email already exists in the database."""
        if UserModel.query.filter_by(email=field.data).first():
            raise ValidationError("This email is already registered. Please use a different email.")
    
    def validate_id_number(self, field):
        """Check if the ID number already exists in the database."""
        if UserModel.query.filter_by(id_number=field.data).first():
            raise ValidationError("This ID number is already registered. Please use a different ID number.")


class ExtendedLoginForm(LoginForm):
    email = EmailField('Please enter your Email', validators=[DataRequired(message="Email is required!")],render_kw={'placeholder':'hello@reallygreatsite.com'})
    password = PasswordField('Please enter Password', validators=[DataRequired(message="Password is required!")], render_kw={'placeholder':'******'})



# class ExtendedSendConfirmationForm(SendConfirmationForm):
#     email = EmailField('Please enter your Email', validators=[DataRequired()],render_kw={'placeholder':'hello@reallygreatsite.com'})






