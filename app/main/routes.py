import requests
from flask import Blueprint, render_template, redirect, url_for, flash,request
from flask_security import login_required, current_user, roles_accepted
from ..utils import db
from app.main.forms import ProfileForm, AddMemberForm, AddCommitteForm, UmbrellaForm, BlockForm, ZoneForm, ScheduleForm
from .models import UserModel, BlockModel, ZoneModel, user_datastore,Role,PaymentModel,MeetingModel
from PIL import Image
import os
import secrets
from app import create_app as app
from flask import current_app



main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.statistics'))
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

  # API call to get user details
    try:
        user = get_user_from_api(current_user.id)
        if user:
            # Autofill form fields with user data
            profile_form.full_name.data = user.get('full_name', '')
            profile_form.id_number.data = user.get('id_number', '')
            profile_form.email.data = user.get('email', '')
        else:
            flash('Unable to load user data.', 'danger')
    except Exception as e:
        flash('Error loading user details. Please try again later.', 'danger')

    # API call to get umbrella by user
    try:
        umbrella = get_umbrella_by_user(current_user.id)
        if umbrella:
            block_form.parent_umbrella.data = umbrella.get('name', '')

            # API calls to dynamically fetch blocks and zones
            blocks = get_blocks_by_umbrella(umbrella['id'])
            zone_form.parent_block.choices = [(str(block['id']), block['name']) for block in blocks]

            zones = []
            for block in blocks:
                zones.extend(get_zones_by_block(block['id']))
            member_form.member_zone.choices = [(str(zone['id']), zone['name']) for zone in zones]
        else:
            blocks, zones = [], []
            flash('No umbrella found. Please create one first.', 'info')
    except Exception as e:
        flash('Error loading umbrella data. Please try again later.', 'danger')

    # API call to get banks
    try:
        banks = get_banks()
        member_form.bank.choices = [(str(bank['id']), bank['name']) for bank in banks]
    except Exception as e:
        flash('Error loading bank information. Please try again later.', 'danger')


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



def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/images', picture_fn)

    output_size = (125, 125) 
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn




# Handle profile update
def handle_profile_update():
    profile_form = ProfileForm()
    api_url = f"{current_app.config['API_BASE_URL']}/api/v1/users/{current_user.id}"


    if profile_form.validate_on_submit():
        # Initialize the update_data dictionary
        update_data = {}

        # If the user uploaded a picture, handle that first
        if profile_form.picture.data:

            try:
                picture_file = save_picture(profile_form.picture.data)
                image_path = os.path.join('static/images', picture_file)


                # Prepare multipart data for the API
                with open(image_path, 'rb') as f:
                    files = {'picture': (picture_file, f, 'image/png')}
                    response = requests.patch(api_url, files=files)


                if response.status_code == 200:
                    flash('Profile picture updated successfully!', 'success')
                    # Update the current user's image_file
                    current_user.image_file = picture_file
                else:
                    flash('Failed to update profile picture.', 'danger')

            except Exception as e:
                flash('An error occurred while updating the profile picture.', 'danger')

        else:
            # If no picture is uploaded, validate the other fields
            if profile_form.full_name.data or profile_form.id_number.data or profile_form.email.data or profile_form.password.data:

                # Collect the fields to update
                if profile_form.full_name.data:
                    update_data['full_name'] = profile_form.full_name.data
                if profile_form.email.data:
                    update_data['email'] = profile_form.email.data
                if profile_form.password.data and len(profile_form.password.data) >= 6:
                    update_data['password'] = profile_form.password.data

                # Skip id_number validation since it's not editable
                if update_data:
                    response = requests.patch(api_url, json=update_data)
                    if response.status_code == 200:
                        flash('Profile updated successfully!', 'success')
                    else:
                        flash('Failed to update profile.', 'danger')
                else:
                    flash('No changes made to the profile.', 'info')

            else:
                flash('No changes made to the profile.', 'info')
    else:
        for field, errors in profile_form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')
    return render_settings_page(active_tab='profile')




# Handle committee addition
def handle_committee_addition():
    committee_form = AddCommitteForm()

    if committee_form.validate_on_submit():
        id_number = committee_form.id_number.data
        role_name = committee_form.role.data

        # Fetch user by ID number
        user = get_user_by_id_number(id_number)

        if user:
            # Check if user already has the "Member" role
            if 'Member' not in user['roles']:
                flash(f"{user['full_name']} must first be a member before being assigned a committee role.", 'danger')
                return redirect(url_for('main.settings', active_tab='committee'))

            # Check if the user already has the committee role
            if role_name in user['roles']:
                flash(f"{user['full_name']} is already a {role_name}!", 'danger')
                return redirect(url_for('main.settings', active_tab='committee'))

            # Retrieve the role to assign
            committee_role = user_datastore.find_role(role_name)

            # If the role exists, assign it to the user
            if committee_role:
                user_datastore.add_role_to_user(user['id'], committee_role)

                # Commit changes to the database
                db.session.commit()

                flash(f"{user['full_name']} added as {role_name} successfully!", 'success')
            else:
                flash(f"Role '{role_name}' does not exist.", 'danger')
        else:
            flash('User not found.', 'danger')

        return redirect(url_for('main.settings', active_tab='committee'))

    # Collect any form errors
    else:
        for field, errors in committee_form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')
    return render_settings_page(active_tab='committee')


# Handle umbrella creation
def handle_umbrella_creation():
    umbrella_form = UmbrellaForm()

    if umbrella_form.validate_on_submit():
        # API call to check existing umbrella
        existing_umbrella = get_umbrella_by_user(current_user.id)
        
        if existing_umbrella:
            flash('You can only create one umbrella!', 'danger')
            return redirect(url_for('main.settings', active_tab='umbrella'))

        create_umbrella({
            'name': umbrella_form.umbrella_name.data,
            'location': umbrella_form.location.data,
            'created_by': current_user.id
        })
        flash('Umbrella created successfully!', 'success')
        return redirect(url_for('main.settings', active_tab='umbrella'))

    else:
        for field, errors in umbrella_form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')
    return render_settings_page(active_tab='umbrella')


# Handle block creation using API
def handle_block_creation():
    block_form = BlockForm()
    umbrella = get_umbrella_by_user(current_user.id)

    if umbrella:
        block_form.parent_umbrella.data = umbrella['name']
    else:
        flash('You need to create an umbrella before creating a block!', 'danger')
        return redirect(url_for('main.settings', active_tab='umbrella'))

    if block_form.validate_on_submit():
        # Check for duplicate blocks via the API
        existing_blocks = get_blocks_by_umbrella(umbrella['id'])

        if any(block['name'] == block_form.block_name.data for block in existing_blocks):
            flash('A block with this name already exists in the umbrella!', 'danger')
            return redirect(url_for('main.settings', active_tab='block'))

        # Proceed to create the block via the API
        create_block({
            'name': block_form.block_name.data,
            'parent_umbrella_id': umbrella['id'],
            'created_by': current_user.id
        })
        flash('Block created successfully!', 'success')
        return redirect(url_for('main.settings', active_tab='block'))

    else:
        for field, errors in block_form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')
    return render_settings_page(active_tab='block')

# Handle zone creation using API
def handle_zone_creation():
    zone_form = ZoneForm()
    
    # Retrieve the umbrella for the current user
    umbrella = get_umbrella_by_user(current_user.id)

    if not umbrella:
        flash('You need to create an umbrella before adding a zone!', 'danger')
        return redirect(url_for('main.settings', active_tab='zone'))

    # Fetch blocks associated with the umbrella
    try:
        blocks = get_blocks_by_umbrella(umbrella['id'])
    except Exception as e:
        return "An error occurred while fetching data.", 500  
    
    zone_form.parent_block.choices = [(str(block['id']), block['name']) for block in blocks]

    if not blocks:
        flash('You need to create a block before adding a zone!', 'danger')
        return redirect(url_for('main.settings', active_tab='zone'))

    if zone_form.validate_on_submit():
        existing_zones = get_zones_by_block(zone_form.parent_block.data)

        # Ensure no duplicate zones in the selected block
        if any(zone['name'] == zone_form.zone_name.data for zone in existing_zones):
            flash('A zone with this name already exists in this block!', 'danger')
            return redirect(url_for('main.settings', active_tab='zone'))

        # Proceed to create the zone via the API
        create_zone({
            'name': zone_form.zone_name.data,
            'parent_block_id': zone_form.parent_block.data,
            'created_by': current_user.id
        })
        flash('Zone created successfully!', 'success')
        return redirect(url_for('main.settings', active_tab='zone'))

    else:
        for field, errors in zone_form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')
    return render_settings_page(active_tab='zone')


# Handle member creation
def handle_member_creation():
    member_form = AddMemberForm()

    # Retrieve the umbrella for the current user
    umbrella = get_umbrella_by_user(current_user.id)

    if not umbrella:
        flash('You need to create an umbrella before adding a member!', 'danger')
        return redirect(url_for('main.settings', active_tab='member'))

    # Fetch blocks associated with the umbrella to populate zones
    try:
        blocks = get_blocks_by_umbrella(umbrella['id'])
    except Exception as e:
        current_app.logger.error(f"Error fetching blocks: {e}")
        return "An error occurred while fetching data.", 500  
    
    # Fetch zones associated with the blocks
    zones = []
    for block in blocks:
        zones.extend(get_zones_by_block(block['id']))  

    # Set the choices for the member_zone field in the form
    member_form.member_zone.choices = [(str(zone['id']), zone['name']) for zone in zones]

    banks = get_banks()
    member_form.bank.choices = [(str(bank['id']), bank['name']) for bank in banks]

    if member_form.validate_on_submit():
        # Check for duplicate members via the API
        existing_members = get_members_by_zone(member_form.member_zone.data)

        if any(member['id_number'] == member_form.id_number.data for member in existing_members):
            flash('A member with this ID number already exists in that zone!', 'danger')
            return redirect(url_for('main.settings', active_tab='member'))

        payload = {
            'full_name': member_form.full_name.data,
            'id_number': member_form.id_number.data,
            'phone_number': member_form.phone_number.data,
            'zone_id': member_form.member_zone.data,
            'bank': member_form.bank.data,
            'acc_number': member_form.acc_number.data
        }

        # Create the member via API
        response = requests.post(f"{current_app.config['API_BASE_URL']}/api/v1/users/", json=payload)

        if response.status_code == 201:
          # Retrieve the user ID from the response
            user_id = response.json()['id']

            # Retrieve the "Member" role
            member_role = user_datastore.find_role("Member")

            # Fetch the user using the appropriate method
            user = user_datastore.find_user(id=user_id)  # Correct method to fetch user by ID

            if user:  # Check if user is found
                user_datastore.add_role_to_user(user, member_role)

                # Commit changes to the database
                db.session.commit()

            flash('Member created and assigned Member role successfully!', 'success')
        else:
            flash('Failed to create member.', 'danger')

        return redirect(url_for('main.settings', active_tab='member'))

    # Collect any form errors
    else:
        for field, errors in member_form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')
    return render_settings_page(active_tab='member')



# Helper function to get user by id
def get_user_from_api(user_id):
    response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/users/{user_id}")
    return response.json() if response.status_code == 200 else None

# Helper function to get user by ID number
def get_user_by_id_number(id_number):
    response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/users/", params={'id_number': id_number})
    users = response.json() if response.status_code == 200 else None
    return users[0] if users else None

# Helper function to get umbrella by user
def get_umbrella_by_user(user_id):
    response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/umbrellas/", params={'created_by': user_id})
    umbrellas = response.json() if response.status_code == 200 else None
    return umbrellas[0] if umbrellas else None
    

# Helper function to get blocks of a specific umbrella
def get_blocks_by_umbrella(umbrella_id):
    """Fetches blocks associated with the specified umbrella via API."""
    response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/blocks/", params={'parent_umbrella_id': umbrella_id})
    
    if response.status_code == 200:
        return response.json()  
    else:
        flash('Error retrieving blocks from the server.', 'danger')
        return [] 
    
# Helper function to get zones of a specific block
def get_zones_by_block(block_id):
    """Fetches zones associated with the specified block via API."""
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/zones/",
            params={'parent_block_id': block_id},
            headers=headers,
            timeout=10
        )
        
        response.raise_for_status()
        
        # Check if the response is JSON
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            raise ValueError(f"Unexpected content type: {content_type}")

        zones = response.json()
        return zones
    except requests.exceptions.RequestException as e:
        flash('Error retrieving zones from the server. Please try again later.', 'danger')
        return []
    except ValueError as e:
        flash('Error processing server response. Please contact support.', 'danger')
        return []



# Helper function to get members of a specific zone
def get_members_by_zone(zone_id):
    """Fetches members associated with the specified zone via API."""
    response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/members/", params={'zone_id': zone_id})

    if response.status_code == 200:
        return response.json()  
    else:
        flash('Error retrieving members from the server.', 'danger')
        return [] 

# Helper function to get banks
def get_banks():
    response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/banks/")
    return response.json() if response.status_code == 200 else []



# Helper function to create an umbrella
def create_umbrella(payload):
    response = requests.post(f"{current_app.config['API_BASE_URL']}/api/v1/umbrellas/", json=payload)
    return response.status_code == 201

# Helper function to create a block
def create_block(payload):
    response = requests.post(f"{current_app.config['API_BASE_URL']}/api/v1/blocks/", json=payload)
    return response.status_code == 201

# Helper function to create a zone
def create_zone(payload):
    response = requests.post(f"{current_app.config['API_BASE_URL']}/api/v1/zones/", json=payload)
    return response.status_code == 201





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

    members = UserModel.query.filter_by(zone_id=schedule_form.zone.data).all()
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

    members = UserModel.query.filter_by(zone_id=schedule_form.zone.data).all()
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
                members = UserModel.query.filter_by(zone_id=schedule_form.zone.data,roles=roles).all()
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
    .join(ZoneModel, UserModel.zone_id == ZoneModel.name)  
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