from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, IntegerField, SubmitField,DateField
from flask_wtf.file import FileField,FileAllowed
from wtforms.validators import DataRequired, Length, ValidationError,NumberRange,Email
from ..api.api import UserModel
from datetime import datetime
from flask_security import current_user

class AddMemberForm(FlaskForm):
    full_name = StringField('Member Full Name',validators=[DataRequired(), Length(max=100,min=5)],render_kw={'placeholder':'John Doe'})
    id_number = IntegerField('Member ID Number',validators=[DataRequired(),NumberRange(min=10000000, max=99999999, message="ID number must be exactly 8 digits.")],render_kw={'placeholder':'xxxxxxxx'})
    phone_number = StringField('Phone Number',validators=[DataRequired(),Length(min=10, max=16, message="Phone number must be between 10 and 16 digits.")],render_kw={'placeholder':'0700000000'})
    member_zone = SelectField('Member Zone', validators=[DataRequired()])
    bank = SelectField('Select Bank',validators=[DataRequired()])
    acc_number = IntegerField('Bank Account Number',validators=[DataRequired()],render_kw={'placeholder':'xxxxxx'})
    submit = SubmitField('SAVE')
    
    def validate_id_number(self,field):
        user = UserModel.query.filter_by(id_number=field.data).first()
        if user:
            raise ValidationError('Member ID already exists')
    
    def validate_phone_number(self, field):
        user = UserModel.query.filter_by(phone_number=str(field.data)).first()
        if user:
            raise ValidationError('Member phone number already exists')
        
    
    
class ProfileForm(FlaskForm):
    picture = FileField('Update Profile Picture',validators=[FileAllowed(['jpg','jpeg','png'])])
    full_name = StringField('Update Your Full Names',validators=[ Length(max=100,min=10)])
    id_number = IntegerField('Member ID Number',validators=[NumberRange(min=10000000, max=99999999, message="ID number must be exactly 8 digits.")])
    email = StringField('Update Your Email',validators=[Email(message="Invalid email")])
    password = PasswordField('Your Password',validators=[ Length(max=100,min=6),],render_kw={'placeholder':'******'})
    submit = SubmitField('SUBMIT')

    def validate_id_number(self,field):
        user = UserModel.query.filter_by(id_number=field.data).first()
        if user:
            raise ValidationError('Member ID already exists')
        
    def validate_email(self,email):
        if email.data != current_user.email:
            user = UserModel.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError("That email is taken.Please choose a different one!")   
    


class AddCommitteForm(FlaskForm):
    full_name = StringField('Committee Full Name',validators=[DataRequired(), Length(max=100,min=10)],render_kw={'placeholder':'e.g John Doe'})
    id_number = IntegerField('Their ID Number',validators=[DataRequired(),NumberRange(min=10000000, max=99999999, message="ID number must be exactly 8 digits.")],render_kw={'placeholder':'xxxxxxxx'})
    role = SelectField('Role', choices=[('Chairman', 'Chairman'), ('Secretary', 'Secretary')],validators=[DataRequired(message='Please select a valid role!')])
    phone_number = StringField('Phone Number',validators=[DataRequired(),Length(min=10, max=16, message="Phone number must be between 10 and 16 digits.")],render_kw={'placeholder':'0700000000'}) 
    submit = SubmitField('SUBMIT')

    def validate_id_number(self,field):
        user = UserModel.query.filter_by(id_number=field.data).first()
        if user:
            raise ValidationError('Member ID already exists')
    
    def validate_phone_number(self, field):
        user = UserModel.query.filter_by(phone_number=str(field.data)).first()
        if user:
            raise ValidationError('Member phone number already exists')
        
   

class UmbrellaForm(FlaskForm):
    umbrella_name = StringField('Umbrella Name',validators=[DataRequired(), Length(max=100,min=4)],render_kw={'placeholder':'Nyangores'})
    location = StringField('Location',validators=[DataRequired(), Length(max=100,min=4)],render_kw={'placeholder':'xxxxxxx'})
    submit = SubmitField('SUBMIT')


class BlockForm(FlaskForm):
    block_name = StringField('Block Name',validators=[DataRequired(), Length(max=100,min=4)],render_kw={'placeholder':'Block 5'})
    parent_umbrella = StringField('Parent Umbrella', render_kw={'readonly': True}) 
    submit = SubmitField('SUBMIT')


    
class ZoneForm(FlaskForm):
    zone_name = StringField('Zone Name',validators=[DataRequired(), Length(max=100,min=1)],render_kw={'placeholder':'Meja Estate zone'})
    parent_block =  SelectField('Parent Block',validators=[DataRequired()])
    submit = SubmitField('SUBMIT')

    
# END OF SETTINGS FORM


# START OF HOST FORM
class ScheduleForm(FlaskForm):
    block =  SelectField('Select the relevant Block',validators=[DataRequired()])
    zone =  SelectField('Select the zone',validators=[DataRequired()])
    member =  SelectField('Select the member',validators=[DataRequired()])
    date = DateField('Pick the date',validators=[DataRequired()])
    submit = SubmitField('Submit')

    def validate_date(self, field):
        if field.data < datetime.now():
            raise ValidationError('The meeting date cannot be in the past')
        




    

      
