from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError,EqualTo
from app.models.models import UserModel

class AddMemberForm(FlaskForm):
    full_name = StringField('Member Full Name',validators=[DataRequired(), Length(max=100,min=10)],render_kw={'placeholder':'Patrick Cheruiyot'})
    id_number = IntegerField('Member ID Number',validators=[DataRequired()],render_kw={'placeholder':'xxxxxxxx'})
    phone_number = IntegerField('Phone Number',validators=[DataRequired()],render_kw={'placeholder':'0798543234'})
    member_zone = SelectField('Member Zone', choices=[('Zone 1', 'Zone 1'), ('Zone 2', 'Zone 2')],validators=[DataRequired()])
    bank = SelectField('Select Bank', choices=[('Equity', 'Equity'), ('DTB', 'DTB')],validators=[DataRequired()])
    acc_number = IntegerField('Bank Account Number',validators=[DataRequired()],render_kw={'placeholder':'xxxxxx'})
    submit = SubmitField('SAVE')
    
    def validate_id_number(self,id_number):
        user = UserModel.query.filter_by(id_number=id_number.data).first()
        if user:
            raise ValidationError('Member ID already exists')
    
    def validate_phone_number(self, phone_number):
        user = UserModel.query.filter_by(phone_number=phone_number.data).first()
        if user:
            raise ValidationError('Member phone number already exists')
        
    
    
class ProfileForm(FlaskForm):
    full_name = StringField('Update Your Full Names',validators=[DataRequired(), Length(max=100,min=10)],render_kw={'placeholder':'Patrick Cheruiyot'})
    id_number = IntegerField('Update Your ID',validators=[DataRequired()],render_kw={'placeholder':'xxxxxxxx'})
    password = PasswordField('Password',validators=[DataRequired(), Length(max=100,min=6)],render_kw={'placeholder':'******'})
    confirm_password = PasswordField('Confirm Password',validators=[DataRequired(), Length(max=100,min=6),EqualTo('password',message="Passwords do not match!")],render_kw={'placeholder':'******'})
    submit = SubmitField('SUBMIT')

    def validate_id_number(self,id_number):
        user = UserModel.query.filter_by(id_number=id_number.form.data).first()
        if user:
            raise ValidationError('Member ID already exists')
    


class AddCommitteForm(FlaskForm):
    full_name = StringField('Committee Full Name',validators=[DataRequired(), Length(max=100,min=10)],render_kw={'placeholder':'Patrick Cheruiyot'})
    id_number = IntegerField('Their ID Number',validators=[DataRequired()],render_kw={'placeholder':'xxxxxxxx'})
    role = SelectField('Role', choices=[('Chairman', 'Chairman'), ('Secretary', 'Secretary')],validators=[DataRequired()])
    phone_number = IntegerField('Phone Number',validators=[DataRequired()],render_kw={'placeholder':'0798543234'}) 
    submit = SubmitField('SUBMIT')

    def validate_id_number(self,id_number):
        user = UserModel.query.filter_by(id_number=id_number.form.data).first()
        if user:
            raise ValidationError('Member ID already exists')
    
    def validate_phone_number(self, phone_number):
        user = UserModel.query.filter_by(phone_number=phone_number.data).first()
        if user:
            raise ValidationError('Member phone number already exists')
        
   

class UmbrellaForm(FlaskForm):
    umbrella_name = StringField('Umbrella Name',validators=[DataRequired(), Length(max=100,min=4)],render_kw={'placeholder':'Nyangores'})
    location = StringField('Location',validators=[DataRequired(), Length(max=100,min=4)],render_kw={'placeholder':'xxxxxxx'})
    submit = SubmitField('SUBMIT')


class BlockForm(FlaskForm):
    block_name = StringField('Block Name',validators=[DataRequired(), Length(max=100,min=4)],render_kw={'placeholder':'Block 5'})
    parent_umbrella = SelectField('Parent Umbrella', choices=[('Nyangores', 'Nyangores'), ('Meja', 'Meja')],validators=[DataRequired()])
    submit = SubmitField('SUBMIT')


    
class ZoneForm(FlaskForm):
    zone_name = StringField('Zone Name',validators=[DataRequired(), Length(max=100,min=4)],render_kw={'placeholder':'Meja Estate zone'})
    parent_block =  SelectField('Parent Block', choices=[('Block 1', 'Block 1'), ('Block 2', 'Block 2')],validators=[DataRequired()])
    submit = SubmitField('SUBMIT')

    
