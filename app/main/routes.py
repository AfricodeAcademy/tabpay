import requests
from flask import Blueprint, render_template, redirect, url_for, flash,request,jsonify
from flask_security import login_required, current_user, roles_accepted
from app.main.forms import ProfileForm, AddMemberForm, AddCommitteForm, UmbrellaForm, BlockForm, ZoneForm, ScheduleForm, EditMemberForm
from .models import UserModel, BlockModel,RoleModel
import logging
import os
from ..utils import save_picture
from flask import current_app
from datetime import datetime,timedelta



main = Blueprint('main', __name__)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@main.route('/', methods=['GET'])
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.statistics'))
    return render_template('index.html')

@main.errorhandler(403)
def forbidden_error(error):
    flash('You must log in to access this page.', 'warning')
    return redirect(url_for('security.login'))


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
            committee_form.block_id.choices = [(str(block['id']), block['name']) for block in blocks]

            # Prepare a mapping for zones with block names
            zone_map = {}  # Store a mapping of zone_id to (zone_name, block_name)
            for block in blocks:
                # Fetch zones associated with the current block
                block_zones = get_zones_by_block(block['id'])
                block_name = block['name']  # Get block name from the block data
                for zone in block_zones:
                    zone_map[zone['id']] = (zone['name'], block_name)  # Store both zone name and block name

            # Set the choices for the member_zone field in the form
            member_form.member_zone.choices = [(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]

        else:
            flash('No umbrella found. Please create one first.', 'info')
    except Exception as e:
        flash('Error loading umbrella data. Please try again later.', 'danger')

    # API call to get banks
    try:
        banks = get_banks()
        member_form.bank_id.choices = [(str(bank['id']), bank['name']) for bank in banks]
    except Exception as e:
        flash('Error loading bank information. Please try again later.', 'danger')

    try:
        roles = get_roles()
        filtered_roles = [role for role in roles if role['id'] in [3, 4, 6]]
        
        if filtered_roles:
            committee_form.role_id.choices = [(str(role['id']), role['name']) for role in filtered_roles]

    except Exception as e:
        flash('Error loading role information. Please try again later.', 'danger')
        print(f'Error:{e}')



    # Render the settings page
    return render_template('settings.html', title=' Settings | Dashboard',
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
@roles_accepted('Admin', 'SuperUser', 'Chairman', 'Secretary','Treasurer')
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
    api_url = f"{current_app.config['API_BASE_URL']}/api/v1/users/{current_user.id}"

    # Log form validation status
    logger.info("Profile update request received. Validating form...")

    if profile_form.validate_on_submit():
        logger.info("Form validated successfully.")

        update_data = {}
        user_changed = False  # To track if any changes are made

        # Handle profile picture update
        if profile_form.picture.data:
            try:
                picture_file = save_picture(profile_form.picture.data)
                image_path = os.path.join(current_app.root_path, 'static/images', picture_file)

                if current_user.image_file != picture_file:
                    # Prepare multipart data for the API request
                    with open(image_path, 'rb') as f:
                        files = {'picture': (picture_file, f, 'image/png')}
                        response = requests.patch(api_url, files=files)

                    if response.status_code == 200:
                        flash('Profile picture updated successfully!', 'success')
                        current_user.image_file = picture_file
                        user_changed = True
                    else:
                        flash('Failed to update profile picture.', 'danger')
                else:
                    flash('The new profile picture is the same as the current one.', 'info')

            except Exception as e:
                flash('An error occurred while updating the profile picture.', 'danger')


        # Handle other profile field updates (name, email, phone number)
        if (profile_form.full_name.data != current_user.full_name or
            profile_form.email.data != current_user.email or
            profile_form.phone_number.data != current_user.phone_number):
            
            logger.info("Processing other profile fields for update.")

            # Collect the fields to update if they are different
            if profile_form.full_name.data and profile_form.full_name.data != current_user.full_name:
                update_data['full_name'] = profile_form.full_name.data
            if profile_form.email.data and profile_form.email.data != current_user.email:
                update_data['email'] = profile_form.email.data
            if profile_form.phone_number.data and profile_form.phone_number.data != current_user.phone_number:
                update_data['phone_number'] = profile_form.phone_number.data

            # Make API call to update the profile fields
            if update_data:
                try:
                    response = requests.patch(api_url, json=update_data)
                    if response.status_code == 200:
                        logger.info("Profile fields updated successfully via API.")
                        flash("Profile updated successfully!", "success")
                        user_changed = True
                    else:
                        logger.error(f"Failed to update profile fields: {response.status_code} - {response.text}")
                        errors = response.json().get('message', "An error occurred")
                        flash(errors, "danger")
                except Exception as e:
                    logger.error(f"Error while updating profile fields: {e}")
                    flash(f"An error occurred: {e}", "danger")
        else:
            logger.info("No changes made to profile fields.")
            flash("No changes made to the profile details.", "info")
        
        if not user_changed:
            logger.info("No updates were made to the profile.")
            flash('No changes made to your profile.', 'info')
        
    else:
        for field, errors in profile_form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')

    return render_settings_page(active_tab='profile')


def get_roles():
    response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/roles/")
    return response.json() if response.status_code == 200 else None    

# Helper function to get user by ID number
def get_user_by_id_number(id_number):
    try:
        response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/users/", params={'id_number': id_number})
        current_app.logger.debug(f"API Response: {response.json()}")  # Log response for debugging
        if response.status_code == 200:
            user = response.json()  # Expecting a single user, not a list
            return user
        return None
    except Exception as e:
        current_app.logger.error(f"Error fetching user by id_number: {e}")
        return None

@main.route('/get_user_by_id_number/<int:id_number>', methods=['GET'])
def get_user(id_number):
    current_app.logger.debug(f"Received GET request for user with ID: {id_number}")
    user = get_user_by_id_number(id_number)  # Reuse your existing function
    if user:
        current_app.logger.debug(f"User found: {user}")
        return jsonify({
            'full_name': user['full_name'],
            'phone_number': user['phone_number'],
            'roles': user.get('roles', [])
        }), 200
    current_app.logger.debug("User not found")
    return jsonify({'error': 'User not found'}), 404


def handle_committee_addition():
    committee_form = AddCommitteForm()

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
    
    committee_form.block_id.choices = [(str(block['id']), block['name']) for block in blocks]

    if not blocks:
        flash('There are no blocks yet!', 'danger')
        return redirect(url_for('main.settings', active_tab='zone'))

    # Fetch available roles
    roles = get_roles()
    
    # Filter for Chairman (id=3), Secretary (id=4), and Treasurer (id=6)
    filtered_roles = [role for role in roles if role['id'] in [3, 4, 6]]
    
    if filtered_roles:
        committee_form.role_id.choices = [(str(role['id']), role['name']) for role in filtered_roles]

    if committee_form.validate_on_submit():
        id_number = committee_form.id_number.data  
        role_id = int(committee_form.role_id.data)  
        block_id = committee_form.block_id.data 

        # Get the role name from the filtered_roles list
        role_name = next((role['name'] for role in filtered_roles if role['id'] == role_id), 'Unknown Role')


        # Fetch user by ID number via API
        user = get_user_by_id_number(id_number)

        if user:
            # Ensure 'roles' is a list before checking the role
            user_roles = user.get('roles', [])
            if not isinstance(user_roles, list):
                flash(f"Oops!An unexpected error occurred.", 'danger')
                return redirect(url_for('main.settings', active_tab='committee'))

            # Check if user has the "Member" role
            if not any(role.get('name') == 'Member' for role in user_roles):
                flash(f"{user['full_name']} must first be a member before being assigned a committee role.", 'danger')
                return redirect(url_for('main.settings', active_tab='committee'))
            
            # Check if the user belongs to the selected block
            user_belongs_to_block = any(block['id'] == int(block_id) for block in user.get('block_memberships', []))
            if not user_belongs_to_block:
                flash(f"{user['full_name']} is not a member of the selected block.", 'danger')
                return redirect(url_for('main.settings', active_tab='committee'))


            # Check if user already has the selected committee role
            if any(role.get('id') == role_id for role in user_roles):
                flash(f"{user['full_name']} is already assigned a '{role_name}' role !", 'danger')
                return redirect(url_for('main.settings', active_tab='committee'))

            # Check for role conflicts: Chairman <-> Secretary, or Chairman/Secretary <-> Treasurer
            if role_id == 3 and any(role.get('id') in [4, 6] for role in user_roles):
                flash(f"{user['full_name']} has a committee role already.", 'danger')
                return redirect(url_for('main.settings', active_tab='committee'))
            if role_id == 4 and any(role.get('id') in [3, 6] for role in user_roles):
                flash(f"{user['full_name']} has a committee role already.", 'danger')
                return redirect(url_for('main.settings', active_tab='committee'))
            if role_id == 6 and any(role.get('id') in [3, 4] for role in user_roles):
                flash(f"{user['full_name']} has a committee role already.", 'danger')
                return redirect(url_for('main.settings', active_tab='committee'))

         

            # Fetch block details and check for existing committee members
            block_response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/blocks/{block_id}")
            if block_response.status_code == 200:
                block = block_response.json()
                block_name = block['name']

                # Ensure the block doesn't already have a chairman, secretary, or treasurer
                if role_id == 3 and block.get('chairman_id'):
                    flash(f"{block_name} already has a chairman assigned.", 'danger')
                    return redirect(url_for('main.settings', active_tab='committee'))

                if role_id == 4 and block.get('secretary_id'):
                    flash(f"{block_name} already has a secretary assigned.", 'danger')
                    return redirect(url_for('main.settings', active_tab='committee'))

                if role_id == 6 and block.get('treasurer_id'):
                    flash(f"{block_name} already has a treasurer assigned.", 'danger')
                    return redirect(url_for('main.settings', active_tab='committee'))
            else:
                    flash(f"An error occurred while fetching the block: {block_response.json().get('message')}", 'danger')


            try:
                # API PATCH request to update the user's role
                response = requests.patch(
                    f"{current_app.config['API_BASE_URL']}/api/v1/users/{user['id']}",
                    json={"role_id": role_id, 'action': 'add', 'block_id': block_id}  
                )

                # Check if the response is successful
                if response.status_code == 200:
                    flash(f"{user['full_name']} has been assigned '{role_name}' role in {block_name} successfully!", 'success')
                    active_tab = 'chairmen' if role_id == 3 else 'secretaries' if role_id == 4 else 'treasurers'

                    return redirect(url_for('main.committee', active_tab=active_tab))
                else:
                    flash(f"An error occurred: {response.json().get('message')}", 'danger')
                    return redirect(url_for('main.settings', active_tab='committee'))
            
            except Exception as e:
                print ( f'{e}')
                flash(f"Sorry, an error occurred.", 'danger')
                return redirect(url_for('main.settings', active_tab='committee'))
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
            flash('A block with that name already exists in the umbrella!', 'danger')
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
            flash('A zone with that name already exists in this block!', 'danger')
            return redirect(url_for('main.settings', active_tab='zone'))

        # Proceed to create the zone via the API
        create_zone({
            'name': zone_form.zone_name.data,
            'parent_block_id': zone_form.parent_block.data,
            'created_by': current_user.id
        })
        flash('Zone created successfully!', 'success')
        # Persist block selection for convenience
        return redirect(url_for('main.settings', active_tab='zone', block_id=zone_form.parent_block.data))

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
    
    # Prepare a mapping for zones with block names
    zone_map = {}  # Store a mapping of zone_id to (zone_name, block_name)
    for block in blocks:
        # Fetch zones associated with the current block
        block_zones = get_zones_by_block(block['id'])
        block_name = block['name']  # Get block name from the block data
        for zone in block_zones:
            zone_map[zone['id']] = (zone['name'], block_name)  # Store both zone name and block name

    # Set the choices for the member_zone field in the form
    member_form.member_zone.choices = [(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]

    banks = get_banks()
    member_form.bank_id.choices = [(str(bank['id']), bank['name']) for bank in banks]

    if member_form.validate_on_submit():
        # Check for duplicate members via the API
        existing_members = get_members_by_zone(member_form.member_zone.data)

        if any(member['id_number'] == member_form.id_number.data for member in existing_members):
            flash('A member with that ID number already exists!', 'danger')
            return redirect(url_for('main.settings', active_tab='member'))

   
        payload = {
            'full_name': member_form.full_name.data,
            'id_number': member_form.id_number.data,
            'phone_number': member_form.phone_number.data,
            'zone_id': member_form.member_zone.data,
            'bank_id': member_form.bank_id.data,
            'acc_number': member_form.acc_number.data,
            'role_id': 5  # Automatically assign "Member" role
        }

        # Create the member via API
        response = requests.post(f"{current_app.config['API_BASE_URL']}/api/v1/users/", json=payload)

        if response.status_code == 201:
            # Get the zone name using the selected zone_id
            zone_name = zone_map.get(int(member_form.member_zone.data))
            flash(f'{member_form.full_name.data} added to {zone_name} successfully!', 'success')
        else:
            flash('Failed to create member.', 'danger')
        
        # Persist zone selection for convenience
        return redirect(url_for('main.settings', active_tab='member', zone_id=member_form.member_zone.data))
    
    zone_id = request.args.get('zone_id')
    if zone_id:
        member_form.member_zone.data = str(zone_id)

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
        zone_name
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
@roles_accepted('Admin', 'SuperUser', 'Chairman', 'Secretary','Treasurer')
@login_required
def statistics():
    # Define the roles to include
    included_roles = ['Member']

    # Query the users who have any of the roles in the included_roles list
    total_members = UserModel.query.join(UserModel.roles).filter(RoleModel.name.in_(included_roles)).count()

    # Get total number of blocks
    total_blocks = BlockModel.query.count()

    return render_template('statistics.html', title='Statistics | Dashboard ', total_members=total_members,
        total_blocks=total_blocks, user=current_user
    )


@main.route('/manage_contribution', methods=['GET'])
@roles_accepted('Admin', 'SuperUser', 'Chairman', 'Secretary','Treasurer')
@login_required
def manage_contribution():
    
    return render_template('manage_contribution.html', title='Manage Contributions | Dashboard')



# Helper function to render the host page with forms
def render_host_page(active_tab=None, error=None):
    logging.info("Rendering host page...")

    # Instantiate all forms
    schedule_form = ScheduleForm()
    update_form = EditMemberForm()

    if not active_tab:
        active_tab = request.args.get('active_tab', 'schedule_meeting')

     # Call API or database to get upcoming meeting details
    meeting_details = get_upcoming_meeting_details()

    if meeting_details:
        print(meeting_details)  
        meeting_block = meeting_details['meeting_block']
        meeting_zone = meeting_details['meeting_zone']
        host = meeting_details['host']
        when = meeting_details['when']
    else:
        flash("No upcoming meeting found", "warning")
        meeting_block = meeting_zone = host = when = None
    

    try:
        user = get_user_from_api(current_user.id)
        if not user:
            flash('Unable to load user data.', 'danger')
    except Exception as e:
        print(f'User Details Error:{e}')
        flash('Error loading user details. Please try again later.', 'danger')

    blocks, zones, members = [], [], []
    # API call to get umbrella by user
    try:
        umbrella = get_umbrella_by_user(current_user.id)
        if umbrella:

            # API calls to dynamically fetch blocks and zones
            blocks = get_blocks_by_umbrella(umbrella['id'])
            schedule_form.block.choices = [(str(block['id']), block['name']) for block in blocks]

             # Prepare a mapping for zones with block names
            zone_map = {}  # Store a mapping of zone_id to (zone_name, block_name)
            for block in blocks:
                # Fetch zones associated with the current block
                block_zones = get_zones_by_block(block['id'])
                block_name = block['name']  # Get block name from the block data
                for zone in block_zones:
                    zone_map[zone['id']] = (zone['name'], block_name)  # Store both zone name and block name

            # Set the choices for the member_zone field in the form
            schedule_form.zone.choices = [(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]

            # Fetch members
            members = get_members()
            if members:
                schedule_form.member.choices = [(str(member['id']), member['full_name']) for member in members]
            else:
                schedule_form.member.choice = []

        else:
            flash('No umbrella found. Please create one first.', 'info')
    except Exception as e:
        logging.error(f"Error loading umbrella data: {e}", exc_info=True)

        flash(f'Error loading umbrella data. Please try again later.', 'danger')

    # Render the host page
    return render_template('host.html', title='Host | Dashboard',
                           schedule_form=schedule_form,
                           update_form=update_form,
                           user=current_user,
                           blocks=blocks,
                           zones=zones,
                           members=members,
                           active_tab=active_tab,  
                           error=error,meeting_block=meeting_block,host=host,meeting_zone=meeting_zone,when=when)

# Single route to handle all host form submissions
@main.route('/host', methods=['GET', 'POST'])
@roles_accepted('Admin', 'SuperUser', 'Chairman', 'Secretary','Treasurer')
@login_required
def host():
    # Check which form was submitted
    if 'schedule_submit' in request.form:
        return handle_schedule_creation()
    elif 'edit_member_submit' in request.form:  
        user_id = request.args.get('user_id')  
        return update_member(user_id)
    elif 'remove_member_submit' in request.form: 
        if request.form.get('_method') == 'DELETE':
            user_id = request.args.get('user_id')   
            return remove_member(user_id)
        
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

     # Prepare a mapping for zones with block names
    zone_map = {}  # Store a mapping of zone_id to (zone_name, block_name)
    for block in blocks:
        # Fetch zones associated with the current block
        block_zones = get_zones_by_block(block['id'])
        block_name = block['name'] 
        for zone in block_zones:
            zone_map[zone['id']] = (zone['name'], block_name)  # Store both zone name and block name

    # Set the choices for the member_zone field in the form
    schedule_form.zone.choices = [(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]

    # Fetch members filtered by zone
    members = get_members()
    if members:
        schedule_form.member.choices = [(str(member['id']), member['full_name']) for member in members]



    if schedule_form.validate_on_submit():
        block_id = schedule_form.block.data
        zone_id = schedule_form.zone.data
        member_id = schedule_form.member.data

        # Fetch block and member information
        block_name = next((block['name'] for block in blocks if str(block['id']) == block_id), 'Unknown Block')
        member = get_user_from_api(member_id)

        # Check if the selected member belongs to the selected block
        member_belongs_to_block = any(block['id'] == int(block_id) for block in member.get('block_memberships', []))
        if not member_belongs_to_block:
            flash(f"{member['full_name']} is not a member of the selected block.", 'danger')
            return redirect(url_for('main.host', active_tab='schedule_meeting'))

        # Check if the selected zone belongs to the selected block
        if zone_id not in [str(zone['id']) for zone in get_zones_by_block(block_id)]:
            flash(f"Selected zone does not belong to {block_name}.", 'danger')
            return redirect(url_for('main.host', active_tab='schedule_meeting'))

        # Check for existing meetings in any block for this week
        existing_meeting = get_upcoming_meeting_details()
        if existing_meeting:
            flash(f'A meeting has already been scheduled for this week in another block!', 'danger')
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
                flash("Meeting has been scheduled successfully!", "success")
                return redirect(url_for('main.host', active_tab='schedule_meeting'))
            else:
                flash('Meeting scheduling failed. Please try again later.', 'danger')
        except Exception as e:
            print(f"Meeting scheduling error: {e}")
            flash('Error creating meeting. Please try again later.', 'danger')

    # Handle form errors
    for field, errors in schedule_form.errors.items():
        for error in errors:
            flash(f'{error}', 'danger')

    return render_host_page(active_tab='schedule_meeting')


def get_upcoming_meeting_details():
    today = datetime.now()
    week_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = (week_start + timedelta(days=6)).replace(hour=23, minute=59, second=59)

    organizer_id = current_user.id  

    try:
        logging.info(f"Fetching upcoming meetings for organizer_id={organizer_id}, start={week_start}, end={week_end}")

        response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/meetings/",
            params={
                'start': week_start.strftime('%Y-%m-%d'),
                'end': week_end.strftime('%Y-%m-%d'),
                'organizer_id': organizer_id
            }
        )
        logging.info(f"API request sent. Status Code: {response.status_code}")

        if response.status_code == 200:
            meeting_data = response.json()
            logging.info(f"API response received: {meeting_data}")

            if isinstance(meeting_data, list) and len(meeting_data) > 0:
                first_meeting = meeting_data[0]
                block_name = first_meeting.get('meeting_block', 'Unknown Block')
                zone_name = first_meeting.get('meeting_zone', 'Unknown Zone')
                host_name = first_meeting.get('host', 'Unknown Host')
                meeting_date = first_meeting.get('when', 'Unknown Date')

                logging.info(f"Extracted meeting details: Block - {block_name}, Zone - {zone_name}, Host - {host_name}, When - {meeting_date}")
                return {
                    'meeting_block': block_name,
                    'meeting_zone': zone_name,
                    'host': host_name,
                    'when': meeting_date,
                }
            elif isinstance(meeting_data, dict):
                block_name = meeting_data.get('meeting_block', 'Unknown Block')
                zone_name = meeting_data.get('meeting_zone', 'Unknown Zone')
                host_name = meeting_data.get('host', 'Unknown Host')
                meeting_date = meeting_data.get('when', 'Unknown Date')
                return {
                    'meeting_block': block_name,
                    'meeting_zone': zone_name,
                    'host': host_name,
                    'when': meeting_date,
                }
            else:
                logging.warning("No upcoming meetings found or unexpected response format.")
                return None
        else:
            logging.error(f"Failed to fetch data from API. Status Code: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while fetching data from the API: {e}")
        return None




def update_member(user_id):
    update_form = EditMemberForm()

    if update_form.validate_on_submit():
        # Prepare payload to update other member details
        payload = {}

        if update_form.full_name.data:
            payload['full_name'] = update_form.full_name.data

        if update_form.phone_number.data:
            payload['phone_number'] = update_form.phone_number.data

        # Only make the request if there is something to update
        if payload:
            try:
                response = requests.patch(f"{current_app.config['API_BASE_URL']}/api/v1/users/{user_id}", json=payload)
                if response.status_code == 200:
                    flash("Member details updated successfully.", "success")
                    return redirect(url_for('main.host', active_tab='block_members'))
                else:
                    flash("Failed to update member details. Please try again.", "danger")
                    return redirect(url_for('main.host', active_tab='block_members'))


            except Exception as e:
                flash("Error updating member details. Please try again later.", "danger")
                return redirect(url_for('main.host', active_tab='block_members'))


        else:
            flash("No changes were made to the member details.", "info")
            return redirect(url_for('main.host', active_tab='block_members'))



    # Handle form validation errors
    for field, errors in update_form.errors.items():
        for error in errors:
            flash(f'{field}: {error}', 'danger')



# Function to handle member removal
def remove_member(user_id):
    # Fetch user details first
    user_response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/users/{user_id}")
    
    if user_response.status_code == 200:
        user_data = user_response.json()
        full_name = user_data.get('full_name')
        
        # Proceed with the delete request
        delete_response = requests.delete(f"{current_app.config['API_BASE_URL']}/api/v1/users/{user_id}")
        
        if delete_response.status_code == 200:
            flash(f"{full_name} removed successfully.", 'success')
        else:
            flash(f'Failed to remove {full_name}! Please drop the assigned role or meeting first.', 'danger')
    else:
        flash('Failed to retrieve user details', 'danger')
    
    return redirect(url_for('main.host', active_tab='block_members'))


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
        logger.error(f"Exception during fetching members: {str(e)}")
        return []


# Fetch and display committee members
def render_committee_page(active_tab=None, error=None):
    # Fetch Chairman, Secretary, and Treasurer from the API
    try:
        chairman_response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/users/", params={'role': 'Chairman'})
        secretary_response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/users/", params={'role': 'Secretary'})
        treasurer_response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/users/", params={'role': 'Treasurer'})

        # Raise exception if request failed
        chairman_response.raise_for_status()
        secretary_response.raise_for_status()
        treasurer_response.raise_for_status()

        # Parse the response
        committee_members = {
            'chairmen': chairman_response.json(),
            'secretaries': secretary_response.json(),
            'treasurers': treasurer_response.json()
        }

        return render_template('committee.html', title='Committee | Dashboard', 
                               committee_members=committee_members, 
                               active_tab=active_tab,
                                 error=error)

    except requests.exceptions.RequestException as e:
        flash(f"Error fetching committee members: {str(e)}", 'danger')
        return redirect(url_for('main.committee'))

# Single route to handle committee-related actions
@main.route('/committee', methods=['GET', 'POST'])
@roles_accepted('Admin', 'SuperUser')
@login_required
def committee():    
    if 'remove_role_submit' in request.form:
        user_id = request.args.get('user_id')  
        active_tab = request.form.get('active_tab')  
        return remove_committee_role(user_id, active_tab)  

    return render_committee_page(active_tab=request.args.get('active_tab', 'chairmen'))


# Remove committee role (Chairman, Secretary, Treasurer)
def remove_committee_role(user_id, active_tab):
    logger.info(f"Removing role for user_id: {user_id}")
    if not user_id:
        flash('User ID is missing.', 'danger')
        return redirect(url_for('main.committee', active_tab=active_tab))

    try:
        role_id = request.form.get('role_id')
        action = 'remove'
        response = requests.patch(f"{current_app.config['API_BASE_URL']}/api/v1/users/{user_id}", json={'role_id': role_id, 'action': action})
        response.raise_for_status()
        flash('Committee role removed successfully', 'success')
        return redirect(url_for('main.committee', active_tab=active_tab))

    except requests.exceptions.RequestException as e:
        flash(f"Error removing committee role: {str(e)}", 'danger')
        logger.error(f"Request failed: {str(e)}")
        return redirect(url_for('main.committee', active_tab=active_tab))


# Helper function to render the host page with forms
def render_reports_page(active_tab=None, error=None):
    schedule_form = ScheduleForm()

    # API call to get user details
    try:
        user = get_user_from_api(current_user.id)
        if not user:
            flash('Unable to load user data.', 'danger')
    except Exception as e:
        print(f'User Details Error:{e}')
        flash('Error loading user details. Please try again later.', 'danger')
    
    umbrella = get_umbrella_by_user(current_user.id)

    if not umbrella:
        flash('You need to create an umbrella before getting reports!', 'danger')
        return redirect(url_for('main.settings', active_tab='umbrella'))


    # Fetch blocks associated with the umbrella
    blocks = get_blocks_by_umbrella(umbrella['id'])
    schedule_form.block.choices = [(str(block['id']), block['name']) for block in blocks]
     # Prepare a mapping for zones with block names
    zone_map = {}  # Store a mapping of zone_id to (zone_name, block_name)
    for block in blocks:
        # Fetch zones associated with the current block
        block_zones = get_zones_by_block(block['id'])
        block_name = block['name'] 
        for zone in block_zones:
            zone_map[zone['id']] = (zone['name'], block_name)  # Store both zone name and block name

    # Set the choices for the member_zone field in the form
    schedule_form.zone.choices = [(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]


    members = []
    try:
        # Fetch members
        members = get_members()
    except Exception as e:
        flash(f'Error fetching members. Please try again later.', 'danger')

    # Render the host page
    return render_template('block_reports.html', title='Block_Reports | Dashboard',
                           user=current_user,
                           members=members,
                           schedule_form=schedule_form, 
                           blocks=blocks,                          
                           active_tab=active_tab,  
                           error=error)


@main.route('/block_reports', methods=['GET', 'POST'])
@roles_accepted('Admin', 'SuperUser', 'Chairman', 'Secretary','Treasurer')
@login_required
def block_reports():
    return render_reports_page(active_tab=request.args.get('active_tab', 'block_contribution'))
