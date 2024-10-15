from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, SubmitField,DateTimeField,HiddenField
from flask_wtf.file import FileField,FileAllowed
from wtforms.validators import DataRequired, Length, ValidationError,NumberRange,Email,Optional
from ..api.api import UserModel
from datetime import datetime

class AddMemberForm(FlaskForm):
    full_name = StringField('Member Full Name',validators=[DataRequired(message="Member Full Name is required"), Length(max=100,min=5)],render_kw={'placeholder':'John Doe'})
    id_number = IntegerField('Member ID Number',validators=[DataRequired(message="Member Id is required"),NumberRange(min=10000000, max=99999999, message="ID number must be exactly 8 digits.")],render_kw={'placeholder':'xxxxxxxx'})
    phone_number = StringField('Phone Number',validators=[DataRequired("Phone Number is required"),Length(min=10, max=16, message="Phone number must be between 10 and 16 digits.")],render_kw={'placeholder':'0700000000'})
    member_zone = SelectField('Member Zone', validators=[DataRequired(message="Member Zone is required")])
    bank_id = SelectField('Select Bank',validators=[DataRequired(message="Bank is required")])
    acc_number = IntegerField('Bank Account Number',validators=[DataRequired()],render_kw={'placeholder':'xxxxxx'})
    submit = SubmitField('ADD MEMBER')
    
    def validate_id_number(self,field):
        user = UserModel.query.filter_by(id_number=field.data).first()
        if user:
            raise ValidationError('Member ID already exists')
    
    def validate_phone_number(self, field):
        user = UserModel.query.filter_by(phone_number=str(field.data)).first()
        if user:
            raise ValidationError('Member phone number already exists')
        
    
    
class ProfileForm(FlaskForm):
    picture = FileField('Update Profile Picture',validators=[FileAllowed(['jpg','jpeg','png'],'Images only')])
    full_name = StringField('Update Your Full Names',validators=[ Length(max=100,min=10)])
    id_number = IntegerField('Your ID Number',render_kw={'readonly':True})
    email = StringField('Update Your Email',validators=[Email(message="Invalid email")])
    phone_number = StringField('Add Phone Number',render_kw={'placeholder':'0700000000'})
    submit = SubmitField('UPDATE PROFILE')
 
    


class AddCommitteForm(FlaskForm):
    full_name = StringField("Committee's Full Name")
    block_id =  SelectField("Committee's Block",validators=[DataRequired()])
    id_number = IntegerField("Committee's ID Number",validators=[DataRequired(),NumberRange(min=10000000, max=99999999, message="ID number must be exactly 8 digits.")],render_kw={'placeholder':'xxxxxxxx'})
    role_id =  SelectField('Committee Role', validators=[DataRequired(message='Please select a valid role!')])
    phone_number = StringField("Committee's Phone Number") 
    submit = SubmitField('ADD COMMITTEE')

 

class UmbrellaForm(FlaskForm):
    umbrella_name = StringField('Umbrella Name',validators=[DataRequired(), Length(max=100,min=4)],render_kw={'placeholder':'Nyangores'})
    location = StringField('Location',validators=[DataRequired(), Length(max=100,min=4)],render_kw={'placeholder':'xxxxxxx'})
    submit = SubmitField('CREATE UMBRELLA')


class BlockForm(FlaskForm):
    block_name = StringField('Block Name',validators=[DataRequired(), Length(max=100,min=4)],render_kw={'placeholder':'Block 5'})
    parent_umbrella = StringField('Parent Umbrella', render_kw={'readonly': True}) 
    submit = SubmitField('CREATE BLOCK')


    
class ZoneForm(FlaskForm):
    zone_name = StringField('Zone Name',validators=[DataRequired(), Length(max=100,min=1)],render_kw={'placeholder':'Meja Estate zone'})
    parent_block =  SelectField('Parent Block',validators=[DataRequired()])
    submit = SubmitField('CREATE ZONE')

    
# END OF SETTINGS FORM


# START OF HOST FORM
class ScheduleForm(FlaskForm):
    block = SelectField('Select the relevant Block', validators=[DataRequired()])
    zone = SelectField('Select the zone', validators=[DataRequired()])
    member = SelectField('Select the member', validators=[DataRequired()])
    date = DateTimeField('Pick the date and time', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()])
    submit = SubmitField('SCHEDULE MEETING')

    def validate_date(self, field):
        if field.data < datetime.now():
            raise ValidationError('The meeting date and time cannot be in the past.')

class EditMemberForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=3, max=100)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    id_number = StringField('ID Number', validators=[DataRequired(), Length(min=5, max=20)])
    member_zone = StringField('Member Zone', render_kw={'readonly': True}) 
    bank_id = StringField('Bank', render_kw={'readonly': True}) 
    account_number = StringField('Account Number', render_kw={'readonly': True}) 
    committee_role = SelectField('Roles', choices=[], validators=[Optional()])
        
    submit = SubmitField('Save Changes')