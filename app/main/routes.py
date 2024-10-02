from flask import Blueprint, render_template, redirect, url_for, flash,request
from flask_security import login_required, roles_required, current_user, logout_user,roles_accepted
from flask_security.utils import hash_password
from ..utils import db
from app.main.forms import ProfileForm, AddMemberForm, AddCommitteForm, UmbrellaForm, BlockForm, ZoneForm, ScheduleForm
from ..api.api import UserModel, UmbrellaModel, BlockModel, ZoneModel, user_datastore,Role,PaymentModel,MeetingModel,BankModel
from PIL import Image
import os
import secrets
from app import create_app as app
from datetime import datetime


main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def home():
    return render_template('index.html', title='TabPay | Home')


# Helper function to render the settings page with forms
def render_settings_page(active_tab=None, error=None):
    # Instantiate all forms
    profile_form = ProfileForm()
    umbrella_form = UmbrellaForm()
    committee_form = AddCommitteForm()
    block_form = BlockForm()
    member_form = AddMemberForm()
    zone_form = ZoneForm()

    if not active_tab:
        active_tab = request.args.get('active_tab', 'profile')

    user = UserModel.query.filter_by(id=current_user.id).first()

    if user:
        # Autofill form fields with user data
        profile_form.full_name.data = user.full_name
        profile_form.id_number.data = user.id_number  

    # Dynamically fetch the umbrella created by the current user
    umbrella = UmbrellaModel.query.filter_by(created_by=current_user.id).first()

    if umbrella:
        # If the umbrella exists, set its name in the block form
        block_form.parent_umbrella.data = umbrella.name
    else:
        flash('You need to create an umbrella before managing settings!', 'danger')

    # Dynamically fetch blocks and zones created by the current user
    blocks = BlockModel.query.filter_by(created_by=current_user.id).all()
    zone_form.parent_block.choices = [(str(block.id), block.name) for block in blocks]

    zones = ZoneModel.query.filter_by(created_by=current_user.id).all()
    member_form.member_zone.choices = [(str(zone.id), zone.name) for zone in zones]

    banks = BankModel.query.all()
    member_form.bank.choices = [(str(bank.id), bank.name) for bank in banks]

    
    # Render the settings page
    return render_template('settings.html', title='Dashboard | Settings',
                           profile_form=profile_form, 
                           umbrella_form=umbrella_form,
                           committee_form=committee_form,
                           block_form=block_form,
                           zone_form=zone_form,
                           member_form=member_form,
                           user=current_user,
                           blocks=blocks,
                           zones=zones,
                           active_tab=active_tab,  
                           error=error)

# Single route to handle all settings form submissions
@main.route('/settings', methods=['GET', 'POST'])
@roles_accepted('Admin', 'SuperUser', 'Chairman', 'Secretary')
@login_required
def settings():
    # Check which form was submitted
    if 'profile_submit' in request.form:
        return handle_profile_update()
    elif 'umbrella_submit' in request.form:
        return handle_umbrella_creation()
    elif 'committee_submit' in request.form:
        return handle_committee_addition()
    elif 'block_submit' in request.form:
        return handle_block_creation()
    elif 'zone_submit' in request.form:
        return handle_zone_creation()
    elif 'member_submit' in request.form:
        return handle_member_creation()
    
    # Default GET request rendering the settings page
    return render_settings_page(active_tab=request.args.get('active_tab', 'profile'))

# Handle profile update
def handle_profile_update():
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
            return redirect(url_for('main.settings',active_tab='profile'))
        
    if profile_form.validate_on_submit():
        user = UserModel.query.filter_by(id=current_user.id).first()
        if user:
            user.full_name = profile_form.full_name.data

             # Update password only if provided
            if profile_form.password.data:
                user.password = hash_password(profile_form.password.data)
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('main.settings',active_tab='profile'))

        else:
            flash('User not found!', 'danger')
            return redirect(url_for('main.settings', active_tab='profile'))
    else:
        error = [f"{field.capitalize()}: {error}" for field, errors in profile_form.errors.items() for error in errors]
        return render_settings_page(active_tab='profile', error=error)


# Handle committee addition
def handle_committee_addition():
    committee_form = AddCommitteForm()

    if committee_form.validate_on_submit():
        user = UserModel.query.filter_by(id_number=committee_form.id_number.data).first()
        if not user:
            flash('No member found with that ID!', 'danger')
            return redirect(url_for('main.settings', active_tab='committee'))
        else:
            member_role = Role.query.filter_by(name='Member').first()
            if member_role not in user.roles:
                flash(f'{user.full_name} must first be a member before being assigned a committee role.', 'danger')
                return redirect(url_for('main.settings', active_tab='committee'))

            else:
                role_name = committee_form.role.data  
                existing_role = Role.query.filter_by(name=role_name).first()
                if existing_role in user.roles:
                    flash(f'{user.full_name} is already a {role_name}!', 'danger')
                    return redirect(url_for('main.settings', active_tab='committee'))
                else:
                    role = user_datastore.find_or_create_role(role_name)
                    user_datastore.add_role_to_user(user, role)
                    db.session.commit()
                    flash(f'{user.full_name} added as {role_name}', 'success')
                    return redirect(url_for('main.settings', active_tab='committee'))

    
    error = [f"{field.capitalize()}: {error}" for field, errors in committee_form.errors.items() for error in errors]
    return render_settings_page(active_tab='committee', error=error)


# Handle umbrella creation
def handle_umbrella_creation():
    umbrella_form = UmbrellaForm()

    if umbrella_form.validate_on_submit():
        existing_umbrella = UmbrellaModel.query.filter_by(created_by=current_user.id).first()
        if existing_umbrella:
            flash('You can only create one umbrella!', 'danger')
            return redirect(url_for('main.settings', active_tab='umbrella'))
        else:
            duplicate_umbrella = UmbrellaModel.query.filter_by(name=umbrella_form.umbrella_name.data).first()
            if duplicate_umbrella:
                flash('An umbrella with that name already exists!', 'danger')
                return redirect(url_for('main.settings', active_tab='umbrella'))
            else:
                new_umbrella = UmbrellaModel(
                    name=umbrella_form.umbrella_name.data,
                    location=umbrella_form.location.data,
                    created_by=current_user.id
                )
                db.session.add(new_umbrella)
                db.session.commit()
                flash('Umbrella created successfully!', 'success')
                return redirect(url_for('main.settings', active_tab='umbrella'))    
    error = [f"{field.capitalize()}: {error}" for field, errors in umbrella_form.errors.items() for error in errors]
    return render_settings_page(active_tab='umbrella', error=error)


# Handle block creation
def handle_block_creation():
    block_form = BlockForm()
    umbrella = UmbrellaModel.query.filter_by(created_by=current_user.id).first()

    if not umbrella:
        flash('You need to create an umbrella before adding a block!', 'danger')
        return redirect(url_for('main.settings', active_tab='block'))

    if block_form.validate_on_submit():
        existing_block = BlockModel.query.filter_by(name=block_form.block_name.data, parent_umbrella_id=umbrella.id).first()
        if existing_block:
            flash('A block with that name already exists in this umbrella.', 'danger')
            return redirect(url_for('main.settings', active_tab='block'))
        else:
            new_block = BlockModel(
                name=block_form.block_name.data,
                parent_umbrella_id=umbrella.id,
                created_by=current_user.id
            )
            db.session.add(new_block)
            db.session.commit()
            flash('Block created successfully!', 'success')
            return redirect(url_for('main.settings', active_tab='block'))

    
    error = [f"{field.capitalize()}: {error}" for field, errors in block_form.errors.items() for error in errors]
    return render_settings_page(active_tab='block', error=error)

# Handle zone creation
def handle_zone_creation():
    zone_form = ZoneForm()
    blocks = BlockModel.query.filter_by(created_by=current_user.id).all()
    zone_form.parent_block.choices = [(str(block.id), block.name) for block in blocks]

    if zone_form.validate_on_submit():
        if not blocks:
            flash('You need to create a block before adding a zone!', 'danger')
            return redirect(url_for('main.settings',active_tab='zone'))

        existing_zone = ZoneModel.query.filter_by(
            name=zone_form.zone_name.data,
            parent_block_id=zone_form.parent_block.data
        ).first()
        if existing_zone:
            flash('A zone with that name already exists in this block.', 'danger')
            return redirect(url_for('main.settings', active_tab='zone'))
        else:
            new_zone = ZoneModel(
                name=zone_form.zone_name.data,
                parent_block_id=zone_form.parent_block.data,
                created_by=current_user.id
            )
            db.session.add(new_zone)
            db.session.commit()
            flash('Zone created successfully!', 'success')
            return redirect(url_for('main.settings', active_tab='zone'))
    
    error = [f"{field.capitalize()}: {error}" for field, errors in zone_form.errors.items() for error in errors]
    return render_settings_page(active_tab='zone', error=error)


# Handle member creation
def handle_member_creation():
    member_form = AddMemberForm()
    zones = ZoneModel.query.filter_by(created_by=current_user.id).all()
    member_form.member_zone.choices = [(str(zone.id), zone.name) for zone in zones]

    if member_form.validate_on_submit():
        if not zones:
            flash('You need to create a zone before adding a member!', 'danger')
            return redirect(url_for('main.settings',active_tab='member'))
        
        existing_user = UserModel.query.filter_by(id_number=member_form.id_number.data, zone=member_form.member_zone.data).first()
        if existing_user:
            flash('User with that ID already exists', 'danger')
            return redirect(url_for('main.settings', active_tab='member'))
        else:
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

            flash('Member created successfully!', 'success')
            return redirect(url_for('main.settings', active_tab='member'))
     
    error = [f"{field.capitalize()}: {error}" for field, errors in member_form.errors.items() for error in errors]
    return render_settings_page(active_tab='member', error=error)



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


@main.route('/statistics', methods=['GET'])
@login_required
@roles_accepted('SuperUser', 'Admin')
def statistics():
    # Define the roles to include
    included_roles = ['Member', 'Chairman', 'Secretary','SuperUser']

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


@main.route('/host', methods=['GET','POST'])
def host():
    schedule_form = ScheduleForm()

     # Dynamically fetch the blocks,zones & members created by the current user
    blocks = BlockModel.query.filter_by(created_by=current_user.id).all()
    schedule_form.block.choices = [(str(block.id), block.name) for block in blocks]

    zones = ZoneModel.query.filter_by(created_by=current_user.id).all()
    schedule_form.zone.choices = [(str(zone.id), zone.name) for zone in zones]

    members = UserModel.query.filter_by(zone=schedule_form.zone.data).all()
    schedule_form.member.choices = [(str(member.id), member.full_name) for member in members]

    block = schedule_form.block.data
    
    block = MeetingModel.query.filter_by(block_id=block).first()
    zone = MeetingModel.query.filter_by(block_id=block).first()
    host = MeetingModel.query.filter_by(block_id=block).first()
    when = MeetingModel.query.filter_by(block_id=block).first()
    return render_template('host.html', title='Dashboard | Host', user=current_user,schedule_form=schedule_form,zones=zones, members=members,blocks=blocks,block=block, when=when,host=host,zone=zone)


# Route to schedule a block meeting
@main.route('/host/schedule_meeting', methods=['GET', 'POST'])
@login_required
def schedule_meeting():
    schedule_form = ScheduleForm()

    blocks = BlockModel.query.filter_by(created_by=current_user.id).all()
    schedule_form.block.choices = [(str(block.id), block.name) for block in blocks]

    zones = ZoneModel.query.filter_by(created_by=current_user.id).all()
    schedule_form.zone.choices = [(str(zone.id), zone.name) for zone in zones]

    members = UserModel.query.filter_by(zone=schedule_form.zone.data).all()
    schedule_form.member.choices = [(str(member.id), member.full_name) for member in members]
    
    if schedule_form.validate_on_submit():

        # Dynamically fetch the blocks created by the current user
        blocks = BlockModel.query.filter_by(created_by=current_user.id).all()
        schedule_form.block.choices = [(str(block.id), block.name) for block in blocks]

        if request.method == 'POST':
            # Only filter zones if a block has been selected
            if schedule_form.block.data:
                zones = ZoneModel.query.filter_by(created_by=current_user.id).all()
                schedule_form.zone.choices = [(str(zone.id), zone.name) for zone in zones]
            else:
                zones = ZoneModel.query.all()

            # Only filter members if a zone has been selected
            if schedule_form.zone.data:
                roles = Role.query.filter_by(role='Member').all()
                members = UserModel.query.filter_by(zone=schedule_form.zone.data,roles=roles).all()
                schedule_form.member.choices = [(str(member.id), member.full_name) for member in members]
            else:
                roles = Role.query.filter_by(name='Member').all()
                members = UserModel.query.filter_by(roles=roles).all()

     
            messages = []
            if not blocks:
                messages.append('No blocks available. Please go to the settings page to create one.')
            if not zones:
                messages.append('No zones available for the selected block. Please add zones in settings.')
            if not members:
                messages.append('No members available for the selected zone. Please add members in settings.')

            if messages:
                flash(' '.join(messages), 'danger')
                return redirect(url_for('main.settings'))

            new_meeting = MeetingModel(
                block_id=schedule_form.block.data,
                zone_id=schedule_form.zone.data,
                members=schedule_form.members.data,
                date=schedule_form.date.data,
            )
            db.session.add(new_meeting)
            db.session.commit()
            flash('Meeting scheduled successfully!', 'success')
            return redirect(url_for('main.host'))
    else:
        # If we reach this point, the form was not validated
        for field, errors in schedule_form.errors.items():
            for error in errors:
                flash(f'Error in {field}: {error}', 'danger')
        
        return redirect(url_for('main.host'))
        



@main.route('/block_reports', methods=['GET', 'POST'])
def block_reports():
    block_filter = request.args.get('blocks')
    member_filter = request.args.get('member')
    date_filter = request.args.get('date')

    blocks = BlockModel.query.all()
    members = UserModel.query.all()

    total_contributed_value = db.session.query(db.func.sum(PaymentModel.amount)).scalar() or 0

    contributions_query = PaymentModel.query

    if block_filter:
        block = BlockModel.query.filter_by(name=block_filter).first()
        if block:
            members_in_block = [member.id for member in block.members]
            contributions_query = contributions_query.filter(PaymentModel.payer_id.in_(members_in_block))  

    if member_filter:
        member = UserModel.query.filter_by(full_name=member_filter).first()
        if member:
            contributions_query = contributions_query.filter_by(payer_id=member.id)  

    if date_filter:
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_filter, '%Y-%m-%d')
            contributions_query = contributions_query.filter(PaymentModel.payment_date >= date_obj)  
        except ValueError:
            pass  

    contributions = contributions_query.all()

    total_contributed = sum(contribution.amount for contribution in contributions)

    detailed_contributions = (
    db.session.query(
        ZoneModel.name.label('zone'),
        UserModel.full_name.label('host'),
        PaymentModel.amount.label('contributed_amount')
    )
    .join(UserModel, PaymentModel.payer_id == UserModel.id)  
    .join(ZoneModel, UserModel.zone == ZoneModel.name)  
    .filter(PaymentModel.id.in_([contribution.id for contribution in contributions]))  
    .all()
)

    return render_template(
        'block_reports.html',
        blocks=blocks,
        members=members,
        contributions=contributions,
        total_contributed=total_contributed,
        detailed_contributions=detailed_contributions
    )

