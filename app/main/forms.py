from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, SubmitField,DateTimeField
from flask_wtf.file import FileField,FileAllowed
from wtforms.validators import DataRequired, Length, ValidationError,NumberRange,Email,Optional
from datetime import datetime


class AddMemberForm(FlaskForm):
    full_name = StringField('Member Full Name', validators=[DataRequired(message=" Full Name is required"), Length(max=30, min=5,message="Full name should have atleast 5 characters.")], render_kw={'placeholder': 'e.g John Doe'})
    id_number = IntegerField('Member ID Number', validators=[DataRequired(message="ID number is required"), Length(min=8, max=10, message="ID number must have atleast 8 digits.")], render_kw={'placeholder': 'xxxxxxxx'})
    phone_number = StringField('Phone Number', validators=[DataRequired(message="Phone Number is required"), Length(min=10, max=10, message="Phone number must be exactly 10 digits.")], render_kw={'placeholder': 'e.g 0700000000'})
    member_zone = SelectField('Member Zone', choices=[("", "Choose a Zone")], validators=[DataRequired(message="Zone is required")])
    bank_id = SelectField('Select Bank', choices=[("", "Choose a Bank")], validators=[DataRequired(message="Bank is required")])
    acc_number = StringField('Bank Account Number', validators=[DataRequired(message="Account Number is required")], render_kw={'placeholder': 'xxxxxx'})
    submit = SubmitField('ADD MEMBER')

class ProfileForm(FlaskForm):
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only')])
    full_name = StringField('Update Your Full Names', validators=[Length(max=30, min=10)])
    id_number = IntegerField('Your ID Number', render_kw={'readonly': True})
    email = StringField('Update Your Email', validators=[Email(message="Invalid email")])
    phone_number = StringField('Add Phone Number', render_kw={'placeholder': '0700000000'})
    submit = SubmitField('UPDATE PROFILE')

class AddCommitteForm(FlaskForm):
    full_name = StringField("Committee's Full Name")
    block_id = SelectField("Committee's Block", choices=[("", "Choose a Block")], validators=[DataRequired(message="Please select a Block")])
    id_number = IntegerField("Committee's ID Number", validators=[DataRequired(message="ID number is required"), NumberRange(min=10000000, max=99999999, message="ID number must be exactly 8 digits.")], render_kw={'placeholder': 'xxxxxxxx'})
    role_id = SelectField('Committee Role', choices=[("", "Choose a Committee Role")], validators=[DataRequired(message="Please select a committee role!")])
    phone_number = StringField("Committee's Phone Number")
    submit = SubmitField('ADD COMMITTEE')

class UmbrellaForm(FlaskForm):
    umbrella_name = StringField('Umbrella Name', validators=[DataRequired(message="Umbrella name is required"), Length(max=30, min=4)], render_kw={'placeholder': 'e.g Nyangores'})
    location = StringField('Location', validators=[DataRequired(message="Umbrella location is required"), Length(max=30, min=4)], render_kw={'placeholder': 'e.g Bomet'})
    submit = SubmitField('CREATE UMBRELLA')

class BlockForm(FlaskForm):
    block_name = StringField('Block Name', validators=[DataRequired(message="Block name is required"), Length(max=30, min=4)], render_kw={'placeholder': 'e.g Block 1'})
    parent_umbrella = StringField('Parent Umbrella', render_kw={'readonly': True})
    submit = SubmitField('CREATE BLOCK')

class ZoneForm(FlaskForm):
    zone_name = StringField('Zone Name', validators=[DataRequired(message="Zone name is required"), Length(max=30, min=4)], render_kw={'placeholder': 'e.g Zone A'})
    parent_block = SelectField('Parent Block', choices=[("", "Choose a Block")], validators=[DataRequired(message="Parent Block is required")])
    submit = SubmitField('CREATE ZONE')

class EditMemberForm(FlaskForm):
    full_name = StringField('Full Name', validators=[Length(max=30, min=5,message="Full name should have atleast 5 characters.")])
    phone_number = StringField('Phone Number', validators=[Length(min=10, max=10, message="Phone number must be exactly 10 digits.")])
    id_number = IntegerField('ID Number', validators=[NumberRange(min=10000000, max=99999999, message="ID number must be exactly 8 digits.")])
    member_zone = SelectField('Select Additional Zone', choices=[("", "Choose a Zone")], validators=[Optional()])
    block_id = SelectField('Select Additional Block', choices=[("", "Choose a Block")], validators=[Optional()])
    bank_id = SelectField('Bank',  validators=[Optional()], render_kw={'readonly': True})
    account_number = StringField('Account Number', validators=[Optional()], render_kw={'readonly': True})
    submit = SubmitField('Save Changes')

class PaymentForm(FlaskForm):
    block = SelectField('Select Block', choices=[("", "Choose a Block")], validators=[DataRequired(message="Block field is required.")])
    member = SelectField('Select Block member', choices=[("", "Choose a Member")], validators=[DataRequired(message="Member field is required .")])
    amount = IntegerField('Amount to Send', validators=[DataRequired(message="Amount field is required.")])
    bank = SelectField('Bank:', choices=[("", "Choose a Bank")], validators=[DataRequired(message="Bank field is required")])
    acc_number = StringField('A/C:', validators=[DataRequired(message="Account number is required.")], render_kw={'placeholder': 'xxxxxx'})
    submit = SubmitField('SEND PAYMENT')
class ScheduleForm(FlaskForm):
    block = SelectField(
        'Select the relevant Block', 
        choices=[("", "Choose a Block")], 
        validators=[DataRequired(message="Please select a block.")]
    )
    zone = SelectField(
        'Select the zone', 
        choices=[("", "Choose a Zone")], 
        validators=[DataRequired(message="Please select a zone.")]
    )
    member = SelectField(
        'Select the member', 
        choices=[("", "Choose a Member")], 
        validators=[DataRequired(message="Please select a member.")]
    )
    date = DateTimeField(
        'Pick the date and time', 
        format='%Y-%m-%d %H:%M:%S', 
        validators=[DataRequired(message="Please pick a date and time.")]
    )
    submit = SubmitField('SCHEDULE MEETING')

    def validate_date(self, field):
        if field.data < datetime.now():
            raise ValidationError('The meeting date and time cannot be in the past.')

