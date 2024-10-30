from flask_security.forms import ConfirmRegisterForm,LoginForm,RegisterForm
from wtforms import StringField,IntegerField,EmailField, PasswordField
from wtforms.validators import DataRequired, Length,ValidationError
from ..api.api import UserModel


class ExtendedRegisterForm(RegisterForm):
    name = StringField('Name',  validators=[DataRequired(), Length(min=4, max=20)],render_kw={'placeholder':'Can even be Umbrella name'})
    email = EmailField('Please enter your Email', validators=[DataRequired()],render_kw={'placeholder':'hello@reallygreatsite.com'})
    password = PasswordField('Please enter Password', validators=[DataRequired()], render_kw={'placeholder':'******'})


class ExtendedConfirmRegisterForm(ConfirmRegisterForm):
    name = StringField('Name',  validators=[DataRequired(), Length(min=4, max=20)],render_kw={'placeholder':'Can even be Umbrella name'})
    email = EmailField('Please enter your Email', validators=[DataRequired()],render_kw={'placeholder':'hello@reallygreatsite.com'})
    password = PasswordField('Please enter Password', validators=[DataRequired()], render_kw={'placeholder':'******'})
    
        

class ExtendedLoginForm(LoginForm):
    email = EmailField('Please enter your Email', validators=[DataRequired()],render_kw={'placeholder':'hello@reallygreatsite.com'})
    password = PasswordField('Please enter Password', validators=[DataRequired()], render_kw={'placeholder':'******'})



# class ExtendedSendConfirmationForm(SendConfirmationForm):
#     email = EmailField('Please enter your Email', validators=[DataRequired()],render_kw={'placeholder':'hello@reallygreatsite.com'})






