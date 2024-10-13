import requests
from flask import Blueprint, render_template, redirect, url_for, flash,request
from flask_security import login_required, current_user, roles_accepted
from ..utils import db
from app.main.forms import ProfileForm, AddMemberForm, AddCommitteForm, UmbrellaForm, BlockForm, ZoneForm, ScheduleForm
from .models import UserModel, BlockModel, ZoneModel, user_datastore,RoleModel,PaymentModel,MeetingModel
from PIL import Image
import os
import logging
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

    blocks, zones =  [], []
    # API call to get umbrella by user
    try:
        umbrella = get_umbrella_by_user(current_user.id)
        if umbrella:
            block_form.parent_umbrella.data = umbrella.get('name', '')

            # API calls to dynamically fetch blocks and zones
            blocks = get_blocks_by_umbrella(umbrella['id'])
            zone_form.parent_block.choices = [(str(block['id']), block['name']) for block in blocks]

            for block in blocks:
                zones.extend(get_zones_by_block(block['id']))
            member_form.member_zone.choices = [(str(zone['id']), zone['name']) for zone in zones]
        else:
            flash('No umbrella found. Please create one first.', 'info')
    except Exception as e:
        flash('Error loading umbrella data. Please try again later.', 'danger')

    # API call to get banks
    try:
        banks = get_banks()
        member_form.bank.choices = [(str(bank['id']), bank['name']) for bank in banks]
    except Exception as e:
        flash('Error loading bank information. Please try again later.', 'danger')

    try:
        roles = get_roles()
        committee_form.role_id.choices = [(str(role['id']), role['name']) for role in roles]
    except Exception as e:
        flash('Error loading role information. Please try again later.', 'danger')


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



import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to save the profile picture
def save_picture(form_picture):
    try:
        # Generate a random hex for the filename and get the file extension
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext

        # Ensure the directory exists and log the action
        image_dir = os.path.join(current_app.root_path, 'static/images')
        if not os.path.exists(image_dir):
            logging.info(f"Directory {image_dir} does not exist. Creating directory...")
            os.makedirs(image_dir)
        else:
            logging.info(f"Directory {image_dir} already exists.")

        # Create the path to save the image
        picture_path = os.path.join(image_dir, picture_fn)

        # Resize the image and save it
        output_size = (125, 125)
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)

        logging.info(f"Profile picture saved at {picture_path}")
        return picture_fn

    except Exception as e:
        logging.error(f"Error saving picture: {e}")
        raise e

# Handle profile update
def handle_profile_update():
    profile_form = ProfileForm()
    api_url = f"{current_app.config['API_BASE_URL']}/api/v1/users/{current_user.id}"

    # Log form validation status
    logger.info("Profile update request received. Validating form...")

    if profile_form.validate_on_submit():
        logging.info("Form validated successfully.")
    
        update_data = {}

        # Handle profile picture update
        if profile_form.picture.data:
            logging.info("User uploaded a new profile picture.")

            try:
                # Save picture and get the file name
                picture_file = save_picture(profile_form.picture.data)
                image_path = os.path.join(current_app.root_path, 'static/images', picture_file)  # Use absolute path

                # Prepare multipart data for the API request
                with open(image_path, 'rb') as f:
                    files = {'picture': (picture_file, f, 'image/png')}
                    response = requests.patch(api_url, files=files)

                # Check API response
                if response.status_code == 200:
                    logging.info("Profile picture updated successfully via API.")
                    flash('Profile picture updated successfully!', 'success')
                    # Update the current user's image_file
                    current_user.image_file = picture_file
                else:
                    logging.error(f"Failed to update profile picture: {response.status_code} - {response.text}")
                    flash('Failed to update profile picture.', 'danger')

            except Exception as e:
                logging.error(f"Error while updating profile picture: {e}")
                flash('An error occurred while updating the profile picture.', 'danger')

        else:
            logging.info("No profile picture uploaded.")

            # Process other profile fields for updates
            if profile_form.full_name.data or profile_form.email.data or profile_form.password.data:
                logging.info("Processing other profile fields for update.")

                # Collect the fields to update
                if profile_form.full_name.data:
                    update_data['full_name'] = profile_form.full_name.data
                if profile_form.email.data:
                    update_data['email'] = profile_form.email.data

                # Only update the password if it meets the length requirement
                if profile_form.password.data and len(profile_form.password.data) >= 6:
                    update_data['password'] = profile_form.password.data
                elif profile_form.password.data and len(profile_form.password.data) < 6:
                    logging.warning("Password update failed: Password must be at least 6 characters long.")
                    flash('Password must be at least 6 characters long.', 'danger')
                    return render_settings_page(active_tab='profile', error=None)

                if update_data:
                    try:
                        response = requests.patch(api_url, json=update_data)
                        if response.status_code == 200:
                            logging.info("Profile fields updated successfully via API.")
                            flash("Profile updated successfully!", "success")
                        else:
                            logging.error(f"Failed to update profile fields: {response.status_code} - {response.text}")
                            errors = response.json().get('message', "An error occurred")
                            flash(errors, "danger")
                    except Exception as e:
                        logging.error(f"Error while updating profile fields: {e}")
                        flash(f"An error occurred: {e}", "danger")
                else:
                    logging.info("No profile fields to update.")
                    flash('No changes made to the profile.', 'info')

            else:
                logging.info("No changes made to the profile.")
                flash('No changes made to the profile.', 'info')
    else:
        for field, errors in profile_form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')
    return render_settings_page(active_tab='profile')


def get_roles():
    response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/roles/")
    return response.json() if response.status_code == 200 else None    
    
def handle_committee_addition():
    committee_form = AddCommitteForm()

    # Fetch available roles
    roles = get_roles()
    if roles:
        committee_form.role_id.choices = [(str(role['id']), role['name']) for role in roles]

    if committee_form.validate_on_submit():
        id_number = committee_form.id_number.data  # Get the ID number
        role_id = committee_form.role_id.data      # Get the selected role_id

        # Fetch user by ID number via API
        user = get_user_by_id_number(id_number)

        if user:
            # Check if user has the "Member" role
            if not any(role['name'] == 'Member' for role in user['roles']):
                flash(f"{user['full_name']} must first be a member before being assigned a committee role.", 'danger')
                return redirect(url_for('main.settings', active_tab='committee'))

            # Check if user already has the committee role
            if any(role['id'] == role_id for role in user['roles']):
                flash(f"{user['full_name']} is already a {role_id}!", 'danger')
                return redirect(url_for('main.settings', active_tab='committee'))

            # API PATCH request to update the user's role
            try:
                response = requests.patch(
                    f"{current_app.config['API_BASE_URL']}/api/v1/users/{user['id']}/roles/",
                    json={"role_id": role_id}  # Sending role_id in the request body
                )

                # Check if the response is successful
                if response.status_code == 200:
                    flash(f"{user['full_name']} added as {role_id} successfully!", 'success')
                else:
                    flash(f"An error occurred: {response.json().get('message')}", 'danger')

            except Exception as e:
                flash(f"An error occurred while updating the role: {str(e)}", 'danger')

        else:
            flash('User not found.', 'danger')

        return redirect(url_for('main.settings', active_tab='committee'))

    # Handle form errors
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

   
        # Add "Member" role via the API by passing role_id (assuming 'Member' role_id is 1)
        payload = {
            'full_name': member_form.full_name.data,
            'id_number': member_form.id_number.data,
            'phone_number': member_form.phone_number.data,
            'zone_id': member_form.member_zone.data,
            'bank': member_form.bank.data,
            'acc_number': member_form.acc_number.data,
            'role_id': 1  # Automatically assign "Member" role
        }

        # Create the member via API
        response = requests.post(f"{current_app.config['API_BASE_URL']}/api/v1/users/", json=payload)

        if response.status_code == 201:
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
        print('Error retrieving members from the server.', 'danger')
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
    total_members = UserModel.query.join(UserModel.roles).filter(RoleModel.name.in_(included_roles)).count()

    # Get total number of blocks
    total_blocks = BlockModel.query.count()

    return render_template('statistics.html', title='Dashboard | Statistics', total_members=total_members,
        total_blocks=total_blocks, user=current_user
    )


@main.route('/manage_contribution', methods=['GET'])
def manage_contribution():
    
    return render_template('manage_contribution.html', title='Dashboard | Manage Contributions')



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
        detailed_contributions=detailed_contributions,
        title='Dashboard | Block_Reports'
    )


# Helper function to render the host page with forms
def render_host_page(active_tab=None, error=None):
    # Instantiate all forms
    schedule_form = ScheduleForm()

    if not active_tab:
        active_tab = request.args.get('active_tab', 'schedule_meeting')

     # Call API or database to get upcoming meeting details
    meeting_details = get_upcoming_meeting_details(current_user.id)

    if meeting_details:
        print(meeting_details)  # Debugging line to check the meeting details
        block = meeting_details['block']
        zone = meeting_details['zone']
        host = meeting_details['host']
        when = meeting_details['when']
    else:
        flash("No upcoming meeting found", "warning")
        block = zone = host = when = None


    
    # API call to get user details
    try:
        user = get_user_from_api(current_user.id)
        if not user:
            flash('Unable to load user data.', 'danger')
    except Exception as e:
        flash('Error loading user details. Please try again later.', 'danger')

    blocks, zones, members = [], [], []
    # API call to get umbrella by user
    try:
        umbrella = get_umbrella_by_user(current_user.id)
        if umbrella:

            # API calls to dynamically fetch blocks and zones
            blocks = get_blocks_by_umbrella(umbrella['id'])
            schedule_form.block.choices = [(str(block['id']), block['name']) for block in blocks]

            for block in blocks:
                zones.extend(get_zones_by_block(block['id']))
            schedule_form.zone.choices = [(str(zone['id']), zone['name']) for zone in zones]

            # Fetch members
            members = get_members()
            if members:
                schedule_form.member.choices = [(str(member['id']), member['full_name']) for member in members]
            else:
                schedule_form.member.choice = []

        else:
            flash('No umbrella found. Please create one first.', 'info')
    except Exception as e:
        flash(f'Error loading umbrella data. Please try again later.', 'danger')

    # Render the host page
    return render_template('host.html', title='Dashboard | Settings',
                           schedule_form=schedule_form,
                           user=current_user,
                           blocks=blocks,
                           zones=zones,
                           members=members,
                           active_tab=active_tab,  
                           error=error,block=block,host=host,zone=zone,when=when)

# Single route to handle all host form submissions
@main.route('/host', methods=['GET', 'POST'])
@roles_accepted('Admin', 'SuperUser', 'Chairman', 'Secretary')
@login_required
def host():
    # Check which form was submitted
    if 'schedule_submit' in request.form:
        return handle_schedule_creation()
    elif 'edit_member_submit' in request.form:  # Handling member edit submission
        return update_member()
    elif 'remove_member_submit' in request.form:  # Handling member removal submission
        return remove_member()
    
    # Default GET request rendering the host page
    return render_host_page(active_tab=request.args.get('active_tab', 'schedule_meeting'))


# Handle schedule creation
def handle_schedule_creation():
    schedule_form = ScheduleForm()
     # Retrieve the umbrella for the current user
    umbrella = get_umbrella_by_user(current_user.id)

    if not umbrella:
        flash('You need to create an umbrella before scheduling a meeting!', 'danger')
        return redirect(url_for('main.settings', active_tab='umbrella'))

    # Fetch blocks associated with the umbrella
    blocks = get_blocks_by_umbrella(umbrella['id'])
    schedule_form.block.choices = [(str(block['id']), block['name']) for block in blocks]

    # Fetch zones for the blocks
    zones = []
    for block in blocks:
        zones.extend(get_zones_by_block(block['id']))
    schedule_form.zone.choices = [(str(zone['id']), zone['name']) for zone in zones]

    # Fetch members filtered by zone
    members = get_members()
    if members:
        schedule_form.member.choices = [(str(member['id']), member['full_name']) for member in members]

    if schedule_form.validate_on_submit():
              # Check for existing meetings in the block
        existing_meetings = get_existing_block_meeting(schedule_form.block.data)
        
        # If any meetings exist for the block, prevent scheduling
        if existing_meetings:  
            flash('A meeting has already been scheduled for this block!', 'danger')
            logger.warning(f"Meeting already scheduled for block ID: {schedule_form.block.data}.")
            return redirect(url_for('main.host', active_tab='schedule_meeting'))


        # Format the date to a string that can be sent in JSON (ISO 8601 format)
        meeting_date_str = schedule_form.date.data.strftime('%Y-%m-%d %H:%M:%S')


        # Payload for creating the meeting
        payload = {
            'block_id': schedule_form.block.data,
            'zone_id': schedule_form.zone.data,
            'host_id': schedule_form.member.data,
            'organizer_id': current_user.id,
            'date': meeting_date_str
        }

        # Create meeting via API
        try:
            response = requests.post(f"{current_app.config['API_BASE_URL']}/api/v1/meetings/", json=payload)
            if response.status_code == 201:
                flash(f"Meeting for {schedule_form.block.data} has created successfully!", "success")
                return redirect(url_for('main.host', active_tab='schedule_meeting'))
            else:
                flash('Meeting creation failed. Please try again later.', 'danger')
        except Exception as e:
            flash('Error creating meeting. Please try again later.', 'danger')

    # Handle form errors
    for field, errors in schedule_form.errors.items():
        for error in errors:
            flash(f'{error}', 'danger')

    return render_host_page(active_tab='schedule_meeting')


# Setup logging (you can configure it further as needed)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Helper function to get upcoming meeting details from the API
def get_upcoming_meeting_details(user_id):
    # API URL for fetching upcoming meetings (update with your actual API URL)
    api_url = f"{current_app.config['API_BASE_URL']}/api/v1/meetings/"
        
    try:
        # Send a GET request to the API
        logging.info(f"Sending GET request to {api_url} with organizer_id={user_id}")
        response = requests.get(api_url, params={'organizer_id': user_id})

        # Check if the request was successful
        if response.status_code == 200:
            meeting_data = response.json()
            logging.info(f"API response received: {meeting_data}")

            # Check if the response is a dictionary rather than a list
            if isinstance(meeting_data, dict):
                block_name = meeting_data.get('block', 'Unknown Block')
                zone_name = meeting_data.get('zone', 'Unknown Zone')
                host_name = meeting_data.get('host', 'Unknown Host')
                meeting_date = meeting_data.get('when', 'Unknown Date')

                logging.info(f"Extracted meeting details: Block - {block_name}, Zone - {zone_name}, Host - {host_name}, When - {meeting_date}")
                return {
                    'block': block_name,
                    'zone': zone_name,
                    'host': host_name,
                    'when': meeting_date
                }
            else:
                logging.warning("No upcoming meetings found or unexpected response format.")
                return None
        else:
            logging.error(f"Failed to fetch data from API. Status Code: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        # Handle any exceptions that occur during the API call
        logging.error(f"An error occurred while fetching data from the API: {e}")
        return None


# Function to handle member edit
def update_member():
    
    members = get_members()


    data = {
        'full_name': request.form['full_name'],
        'phone_number': request.form['phone_number'],
    }
    
    # Assuming you consume an API here to update the member details
    response = requests.patch(f"{current_app.config['API_BASE_URL']}/api/v1/users/",json=data)
    
    if response == 200:
        flash('Member details updated successfully', 'success')
    else:
        flash('Failed to update member details', 'danger')
    
    return render_host_page(active_tab='block_members')


# Function to handle member removal
def remove_member(user_id):
    response = requests.delete(f"{current_app.config['API_BASE_URL']}/api/v1/users/{user_id}")
    
    if response == 200:
        flash('Member removed successfully', 'success')
    else:
        flash('Failed to remove member', 'danger')
    
    return render_host_page(active_tab='block_members')


# Helper function to fetch members by role "Member"
def get_members():
    try:
        logger.info("Fetching users with role 'Member'.")
        # API call to retrieve members based on the role "Member"
        response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/users/", params={'role': 'Member'})
        
        if response.status_code == 200:
            members = response.json()
            logger.info(f"Users fetched successfully: {len(members)} members.")
            return members
        else:
            flash("Error fetching members. Please try again later.", "danger")
            logger.error(f"Error fetching members: Status Code {response.status_code}")
            return []
    except Exception as e:
        flash(f"An error occurred while fetching members: {str(e)}", "danger")
        logger.error(f"Exception during fetching members: {str(e)}")
        return []

# Helper function to check if a meeting already exists for the block
def get_existing_block_meeting(block_id):
    try:
        logger.info(f"Checking for existing meetings for block ID: {block_id}.")
        # API call to check existing meetings for the block
        response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/meetings", params={'block_id': block_id})
        
        if response.status_code == 200:
            meetings = response.json()
            logger.info(f"Meetings found: {len(meetings)}")
            return meetings
        else:
            flash("Error fetching meetings. Please try again later.", "danger")
            logger.error(f"Error fetching meetings: Status Code {response.status_code}")
            return []
    except Exception as e:
        flash(f"An error occurred while fetching meetings: {str(e)}", "danger")
        logger.error(f"Exception during fetching meetings: {str(e)}")
        return []