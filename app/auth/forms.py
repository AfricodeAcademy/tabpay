from flask_security.forms import RegisterForm,ConfirmRegisterForm
from wtforms import StringField,IntegerField
from wtforms.validators import DataRequired, Length

class ExtendedRegisterForm(RegisterForm):
    full_name = StringField('Please enter your Full Names', validators=[DataRequired(), Length(min=4, max=20)],render_kw={'placeholder':'Jiara Martins'})
    id_number = IntegerField('ID No:', validators=[DataRequired()],render_kw={'placeholder':'xxxxxxxx'})


class ExtendedConfirmRegisterForm(ConfirmRegisterForm):
    full_name = StringField('Full Name', [DataRequired()])
    id_number = IntegerField('ID No:', [DataRequired()])





