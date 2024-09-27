from flask import Blueprint, render_template, redirect, url_for, flash,request
from flask_security import login_required, roles_required, current_user, logout_user,roles_accepted
from flask_security.utils import hash_password
from ..utils import db
from app.main.forms import ProfileForm, AddMemberForm, AddCommitteForm, UmbrellaForm, BlockForm, ZoneForm
from ..api.api import UserModel, UmbrellaModel, BlockModel, ZoneModel, user_datastore,Role,MeetingModel,PaymentModel
from PIL import Image
import os
import secrets
from app import create_app as app
from datetime import datetime


main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def home():
    return render_template('index.html', title='TabPay | Home')


@main.route('/settings', methods=['GET','POST'])
@roles_accepted('SuperUser','Umbrella_creator','Chairman','Secretary')
@login_required
def settings():
   
    # Instantiate all forms
    profile_form = ProfileForm()
    umbrella_form = UmbrellaForm()
    committee_form = AddCommitteForm()
    block_form = BlockForm()
    member_form = AddMemberForm()
    zone_form = ZoneForm()


    # Render the settings page
    return render_template('settings.html', title='Dashboard | Settings',
                           profile_form=profile_form, 
                           umbrella_form=umbrella_form,
                           committee_form=committee_form,
                           block_form=block_form,
                           zone_form=zone_form,
                           member_form=member_form,
                           user=current_user
                           )

# Profile Update Route
@main.route('/settings/update_profile', methods=['GET', 'POST'])
@roles_required('Umbrella_creator')
def update_profile():
    profile_form = ProfileForm()

    # Handle GET request - populate form with current user info
    if request.method == 'GET':
        user = UserModel.query.filter_by(id=current_user.id).first()

        if user:
            # Autofill form fields with user data
            profile_form.full_name.data = user.full_name
            profile_form.id_number.data = user.id_number  # The id_number is read-only in the form
        else:
            flash('User not found!', 'danger')
            return redirect(url_for('main.settings'))

    # Handle POST request - update profile
    if profile_form.validate_on_submit():
        user = UserModel.query.filter_by(id=current_user.id).first()
        
        if user:
            user.full_name = profile_form.full_name.data
            
            # Update password only if provided
            if profile_form.password.data:
                user.password = hash_password(profile_form.password.data)
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        else:
            flash('User not found!', 'danger')
    
    elif request.method == 'POST':  # If form validation fails
        error_messages = [f"{field.capitalize()}: {error}" for field, errors in profile_form.errors.items() for error in errors]
        for message in error_messages:
            flash(message, 'danger')
    


# Committee Addition Route
@main.route('/settings/add_committee',  methods=['GET','POST'])
@roles_accepted('Umbrella_creator','SuperUser')
def add_committee():
    committee_form = AddCommitteForm()

    if committee_form.validate_on_submit():
        # Query the database for the user by ID number
        user = UserModel.query.filter_by(id_number=committee_form.id_number.data).first()

        if not user:
            flash('No member found with that ID! ', 'danger')
            return redirect(url_for('main.settings'))
        else:
            # Check if the user has the "Member" role
            member_role = Role.query.filter_by(name='Member').first()
            if member_role not in user.roles:
                flash(f'{user.full_name} must first have the "Member" role before being assigned a committee role.', 'danger')
                return redirect(url_for('main.settings'))
        
            # Check if the user is already a committee member
            role_name = committee_form.role.data  
            existing_role = Role.query.filter_by(name=role_name).first()

            if existing_role in user.roles:
                flash(f'{user.full_name} is already a {role_name}!', 'danger')
            else:
                # # Dynamically populate the form fields with the user's data
                # committee_form.full_name.data = user.full_name
                # committee_form.phone_number.data = user.phone_number

                # Assign the committee role to the user
                role = user_datastore.find_or_create_role(committee_form.role.data)
                user_datastore.add_role_to_user(user, role)
                db.session.commit()
                flash(f'{user.full_name} added as {committee_form.role.data}', 'success')

            return redirect(url_for('main.settings'))
    # Handle GET method to pre-fill form based on the user's input (ID number)
    elif request.method == 'GET' and 'id_number' in request.args:
        user = UserModel.query.filter_by(id_number=request.args.get('id_number')).first()

        if user:
            committee_form.full_name.data = user.full_name
            committee_form.phone_number.data = user.phone_number
        else:
            flash('No member found with that ID!', 'danger')



    flash('Form validation failed, please check your input', 'danger')
    return redirect(url_for('main.settings'))

              
#Umbrella Creation Route
@main.route('/settings/create_umbrella',  methods=['GET','POST'])
@roles_accepted('Umbrella_creator','SuperUser')
def create_umbrella():
    umbrella_form = UmbrellaForm()

    if umbrella_form.validate_on_submit():
        # Check if the user already has an umbrella
        existing_umbrella = UmbrellaModel.query.filter_by(created_by=current_user.id).first()
        if existing_umbrella:
            flash('You can only create one umbrella!', 'danger')
        else:
            # Check if an umbrella with the same name already exists
            duplicate_umbrella = UmbrellaModel.query.filter_by(name=umbrella_form.umbrella_name.data).first()
            if duplicate_umbrella:
                flash('An umbrella with that name already exists!', 'danger')
            else:
                # Proceed to create the umbrella if no duplicates
                new_umbrella = UmbrellaModel(
                    name=umbrella_form.umbrella_name.data,
                    location=umbrella_form.location.data,
                    created_by=current_user.id
                )
                db.session.add(new_umbrella)
                db.session.commit()
                flash('Umbrella created successfully!', 'success')
        return redirect(url_for('main.settings'))

    flash('Form validation failed, please check your input', 'danger')
    return redirect(url_for('main.settings'))


#Block Creation Route
@main.route('/settings/create_block', methods=['GET', 'POST'])
@roles_accepted('Umbrella_creator', 'SuperUser')
def create_block():
    block_form = BlockForm()

    # Automatically retrieve the umbrella created by the current user
    umbrella = UmbrellaModel.query.filter_by(created_by=current_user.id).first()

    if not umbrella:
        flash('You need to create an umbrella before adding a block!', 'danger')
        return redirect(url_for('main.settings'))

    # Pre-fill the umbrella field with the current user's umbrella and make it read-only
    if request.method == 'GET':
        block_form.parent_umbrella.data = umbrella.id  # Pre-fill hidden umbrella field

    if block_form.validate_on_submit():
        # Check if a block with the same name exists within the parent umbrella
        existing_block = BlockModel.query.filter_by(
            name=block_form.block_name.data,
            parent_umbrella_id=umbrella.id
        ).first()

        if existing_block:
            flash('A block with that name already exists in this umbrella.', 'danger')
        else:
            new_block = BlockModel(
                name=block_form.block_name.data,
                parent_umbrella_id=umbrella.id,
                created_by=current_user.id
            )
            db.session.add(new_block)
            db.session.commit()
            flash('Block created successfully!', 'success')
        return redirect(url_for('main.settings'))


#Zone Creation Route
@main.route('/settings/create_zone',  methods=['GET','POST'])
@roles_accepted('Umbrella_creator','SuperUser')
def create_zone():
    zone_form = ZoneForm()
    
    if zone_form.validate_on_submit():

        blocks = BlockModel.query.filter_by(created_by=current_user.id).all()
        if not blocks:
            flash('You need to create a block before adding a zone!', 'danger')
            return redirect(url_for('main.settings'))
        
        # Check if a zone with the same name exists within the parent block
        existing_zone = ZoneModel.query.filter_by(
            name=zone_form.zone_name.data,
            parent_block_id=zone_form.parent_block.data
        ).first()
        
        if existing_zone:
            flash('A zone with that name already exists in this block.', 'danger')
        
        
        else:

            # Dynamically fetch the blocks from the database
            blocks = BlockModel.query.all()

            # Populate the SelectField with block choices
            zone_form.parent_block.choices = [(str(block.id), block.name) for block in blocks]

            new_zone = ZoneModel(
                name=zone_form.zone_name.data,
                parent_block_id=zone_form.parent_block.data,
                created_by=current_user.id
            )
            db.session.add(new_zone)
            db.session.commit()
            flash('Zone created successfully!', 'success')
        return redirect(url_for('main.settings'))
    else:
        flash('Form validation failed', 'danger')
        return redirect(url_for('main.settings'))

#Member Creation Route
@main.route('/settings/add_member',  methods=['GET','POST'])
@roles_required('Umbrella_creator','SuperUser','Chairman','Secretary')
def add_member():
    member_form = AddMemberForm()
    if member_form.validate_on_submit():

        zones = ZoneModel.query.filter_by(created_by=current_user.id).all()
        if not zones:
            flash('You need to create a zone before adding a member!', 'danger')
            return redirect(url_for('main.settings'))
        
        existing_user = UserModel.query.filter_by(id_number=member_form.id_number.data,zone=member_form.member_zone.data).first()
        if existing_user:
            flash('User with that ID already exists', 'danger')
        else:
            # Dynamically fetch the zones from the database
            zones = ZoneModel.query.all()

            # Populate the SelectField with block choices
            AddMemberForm.member_zone.choices = [(str(zone.id), zone.name) for zone in zones]

            new_user = UserModel(
                full_name=member_form.full_name.data,
                id_number=member_form.id_number.data,
                phone_number=member_form.phone_number.data,
                zone=member_form.member_zone.data,
                bank=member_form.bank.data,
                acc_number=member_form.acc_number.data
            )
            db.session.add(new_user)
            db.session.commit()

              # Assign the 'Member' role to the new user
        member_role = user_datastore.find_or_create_role('Member')
        user_datastore.add_role_to_user(new_user, member_role)
        db.session.commit()

        flash('Member added successfully', 'success')
        return redirect(url_for('main.settings'))
    else:
        flash('Form validation failed', 'danger')
        return redirect(url_for('main.settings'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/images', picture_fn)
    
    #This below helps to reduce the file size and make our web faster
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    
    return picture_fn

# @app.route("/account",methods=['POST','GET'])
# @login_required
# def account():
#     form = UpdateAccountForm()
#     if form.validate_on_submit():
#         if form.picture.data:
#             picture_file = save_picture(form.picture.data)
#             current_user.image_file = picture_file
#         current_user.username = form.username.data
#         current_user.email = form.email.data
#         db.session.commit()
#         flash("Your account has been updated!","success")
#         return redirect(url_for('account'))
#     elif request.method == "GET":
#         form.username.data = current_user.username
#         form.email.data = current_user.email
#     image_file = url_for('static',filename='profile_pics/' + current_user.image_file)
#     return render_template('account.html',title='Account',image_file=image_file,form=form)



@main.route('/statistics', methods=['GET'])
@login_required
@roles_accepted('Umbrella_creator', 'SuperUser')
def statistics():
    # Define the roles to include
    included_roles = ['Member', 'Chairman', 'Secretary','Umbrella_creator']

    # Query the users who have any of the roles in the included_roles list
    total_members = UserModel.query.join(UserModel.roles).filter(Role.name.in_(included_roles)).count()

    # Get total number of blocks
    total_blocks = BlockModel.query.count()

    return render_template('statistics.html', title='Dashboard | Statistics', total_members=total_members,
        total_blocks=total_blocks, user=current_user
    )


@main.route('/manage_contribution', methods=['GET'])
def manage_contribution():
    
    return render_template('manage_contribution.html', title='Dashboard | Manage Contributions')


@main.route('/host', methods=['GET'])
def host():
    return render_template('host.html', title='Dashboard | Host')


# Route to schedule a block meeting
@main.route('/host/schedule_meeting', methods=['GET', 'POST'])
@login_required
def schedule_meeting():
    if request.method == 'POST':
        block_id = request.form.get('block_id')
        member_id = request.form.get('member_id')
        zone_id = request.form.get('zone_id')
        meeting_date = request.form.get('meeting_date')

        # Validate form data
        if not block_id or not member_id or not zone_id or not meeting_date:
            flash('All fields are required.', 'error')
            return redirect(url_for('host'))

        try:
            meeting_date = datetime.strptime(meeting_date, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('host'))

        # Check for conflicts
        existing_meeting = MeetingModel.query.filter_by(block_id=block_id, date=meeting_date).first()
        if existing_meeting:
            flash('A meeting is already scheduled for this date.', 'danger')
            return redirect(url_for('host'))

        # Create and save the new meeting
        new_meeting = MeetingModel(block_id=block_id, member_id=member_id, zone_id=zone_id, date=meeting_date)
        db.session.add(new_meeting)
        db.session.commit()

        flash('Meeting successfully scheduled.', 'success')
        return redirect(url_for('host'))

    zone_id = request.args.get('zone_id')
    block_id = request.args.get('block_id')
    blocks = BlockModel.query.all()
    zones = ZoneModel.query.filter_by(block_id=block_id).all()
    
     
    if zone_id:
        members = UserModel.query.filter_by(zone_id=zone_id).all()  
    else:
        members = UserModel.query.filter_by(block_id=block_id).all()  

    return render_template('host.html', blocks=blocks,zones=zones, members=members)

# Route to fetch upcoming block meetings
@main.route('/host/upcoming_meetings', methods=['GET'])
@login_required
def upcoming_meetings():
    date = request.form.get('meeting_date')
    block = MeetingModel.query.filter_by(date=date).first()
    zone = MeetingModel.query.filter_by(date=date).first()
    host = MeetingModel.query.filter_by(date=date).first()
    when = MeetingModel.query.filter_by(date=date).first()
    return render_template('host.html',block=block, when=when,host=host,zone=zone)


@main.route('/host/block_members',methods=['GET', 'POST'])
@login_required
def block_members():
    block_id = request.args.get('block_id')
    zone_id = request.args.get('zone_id')

    if not block_id:
        flash('Block is required.', 'danger')
        return redirect(url_for('host'))

    blocks = BlockModel.query.all()
    zones = ZoneModel.query.filter_by(id=block_id).all()
    members = UserModel.query.filter_by(zone=zone_id).all()

    return render_template(
        'host.html',
        blocks=blocks,
        members=members,zones=zones
    )

# Route to display contribution status of a member
@main.route('/host/contribution_status', methods=['GET'])
@login_required
def contribution_status():
    member_id = request.args.get('member_id', current_user.id)
    contributions = PaymentModel.query.filter_by(member_id=member_id).all()

    total_contributed = sum(contribution.amount for contribution in contributions)

    return render_template(
        'host.html',
        contributions=contributions,
        total_contributed=total_contributed
    )

# Route to display block participation and contribution analytics
@main.route('/host/block_analytics', methods=['GET'])
@login_required
def block_analytics():
    block_id = request.args.get('block_id')

    if not block_id:
        flash('Block ID is required.', 'danger')
        return redirect(url_for('host'))

    block = BlockModel.query.get(block_id)

    total_meetings = MeetingModel.query.filter_by(block_id=block_id).count()
    successful_meetings = MeetingModel.query.filter_by(block_id=block_id, status='successful').count()
    average_participation_rate = successful_meetings / total_meetings if total_meetings > 0 else 0

    return render_template(
        'host.html',
        block=block,
        total_meetings=total_meetings,
        successful_meetings=successful_meetings,
        average_participation_rate=average_participation_rate
    )




@main.route('/block_reports', methods=['GET', 'POST'])
def block_reports():
    block_filter = request.args.get('block')
    member_filter = request.args.get('member')
    date_filter = request.args.get('date')
    
  
    blocks = BlockModel.query.all()
    members = UserModel.query.all()

    
    contributions_query = PaymentModel.query.all()

   
    if block_filter:
        block = BlockModel.query.filter_by(name=block_filter).first()
        if block:
            members_in_block = [member.id for member in block.members]
            contributions_query = contributions_query.filter(Contribution.member_id.in_(members_in_block))

   
    if member_filter:
        member = UserModel.query.filter_by(name=member_filter).first()
        if member:
            contributions_query = contributions_query.filter_by(member_id=member.id)

   
    if date_filter:
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_filter, '%Y-%m-%d')
            contributions_query = contributions_query.filter(Contribution.date >= date_obj)
        except ValueError:
            pass  

  
    contributions = contributions_query.all()

   
    total_contributed = sum(contribution.amount for contribution in contributions)

    
    return render_template(
        'block_reports.html',
        blocks=blocks,
        members=members,
        contributions=contributions,
        total_contributed=total_contributed
    )    


@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))
