from flask_security.forms import ConfirmRegisterForm,LoginForm,RegisterForm
from wtforms import StringField,IntegerField,EmailField, PasswordField
from wtforms.validators import DataRequired, Length,ValidationError
from ..api.api import UserModel


class ExtendedRegisterForm(RegisterForm):
    full_name = StringField('Please enter your Full Names',  validators=[DataRequired(), Length(min=4, max=20)],render_kw={'placeholder':'Jiara Martins'})
    id_number = IntegerField('ID No:', validators=[DataRequired()],render_kw={'placeholder':'xxxxxxxx'})
    email = EmailField('Please enter your Email', validators=[DataRequired()],render_kw={'placeholder':'hello@reallygreatsite.com'})
    password = PasswordField('Please enter Password', validators=[DataRequired()], render_kw={'placeholder':'******'})


    def validate_id_number(self, id_number):
        user = UserModel.query.filter_by(id_number=id_number.data).first()  
        if user:
            raise ValidationError('This ID number is already registered. Please use a different ID number.')
        

class ExtendedConfirmRegisterForm(ConfirmRegisterForm):
    full_name = StringField('Please enter your Full Names',  validators=[DataRequired(), Length(min=4, max=20)],render_kw={'placeholder':'Jiara Martins'})
    id_number = IntegerField('ID No:', validators=[DataRequired()],render_kw={'placeholder':'xxxxxxxx'})
    email = EmailField('Please enter your Email', validators=[DataRequired()],render_kw={'placeholder':'hello@reallygreatsite.com'})
    password = PasswordField('Please enter Password', validators=[DataRequired()], render_kw={'placeholder':'******'})


    def validate_id_number(self, id_number):
        user = UserModel.query.filter_by(id_number=id_number.data).first()  
        if user:
            raise ValidationError('This ID number is already registered. Please use a different ID number.')
        
    
        

class ExtendedLoginForm(LoginForm):
    email = EmailField('Please enter your Email', validators=[DataRequired()],render_kw={'placeholder':'hello@reallygreatsite.com'})
    password = PasswordField('Please enter Password', validators=[DataRequired()], render_kw={'placeholder':'******'})



# class ExtendedSendConfirmationForm(SendConfirmationForm):
#     email = EmailField('Please enter your Email', validators=[DataRequired()],render_kw={'placeholder':'hello@reallygreatsite.com'})






