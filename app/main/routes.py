import requests
from flask import Blueprint, render_template, redirect, url_for, flash,request,jsonify
from flask_security import login_required, current_user, roles_accepted, user_registered
from app.main.forms import ProfileForm, AddMemberForm, AddCommitteForm, UmbrellaForm, BlockForm, ZoneForm, ScheduleForm, EditMemberForm,PaymentForm
import logging
import os
from ..utils import save_picture, db
from flask import current_app
from datetime import datetime,timedelta
from ..utils.send_sms import SendSMS
from app.auth.decorators import approval_required
from functools import wraps


main = Blueprint('main', __name__)

sms = SendSMS()

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
def render_settings_page(active_tab=None,umbrella_form=None,block_form=None,committee_form=None,zone_form=None, member_form=None,error=None):
    # Instantiate all forms
    profile_form = ProfileForm()

    if umbrella_form is None:
        umbrella_form = UmbrellaForm()    
    if block_form is None:
        block_form = BlockForm()
    if zone_form is None:
        zone_form = ZoneForm()
    if member_form is None:
        member_form = AddMemberForm()
    if committee_form is None:
        committee_form = AddCommitteForm()



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
            blocks = get_blocks_by_umbrella()
            zone_form.parent_block.choices = [("", "--Choose Parent Block--")] + [(str(block['id']), block['name']) for block in blocks]
            committee_form.block_id.choices = [("", "--Choose a Block--")] + [(str(block['id']), block['name']) for block in blocks]

            # Prepare a mapping for zones with block names
            zone_map = {}  # Store a mapping of zone_id to (zone_name, block_name)
            for block in blocks:
                # Fetch zones associated with the current block       
                block_id = block['id']         
                block_zones = get_zones_by_block(block_id)
                block_name = block['name']  #_idlock name from the block data
                for zone in block_zones:
                    zone_map[zone['id']] = (zone['name'], block_name)  # Store both zone name and block name

            # Set the choices for the member_zone field in the form
            member_form.member_zone.choices = [("", "--Choose a Zone--")] + [(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]

        else:
            flash('No umbrella found. Please create one first.', 'danger')
    except Exception as e:
        print(f'Settings page Error: {e}')

    # API call to get banks
    try:
        banks = get_banks()
        member_form.bank_id.choices = [("", "--Choose a Bank--")] + [(str(bank['id']), bank['name']) for bank in banks]
    except Exception as e:
        flash('Error loading bank information. Please try again later.', 'danger')

    try:
        roles = get_roles()
        filtered_roles = [role for role in roles if role['id'] in [3, 4, 6]]
        
        if filtered_roles:
            committee_form.role_id.choices = [("", "--Choose a committee role--")] + [(str(role['id']), role['name']) for role in filtered_roles]

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
@login_required
@approval_required
@roles_accepted('SuperUser', 'Administrator')
def settings():
    umbrella_form = UmbrellaForm()
    block_form = BlockForm()
    zone_form = ZoneForm()
    member_form = AddMemberForm()
    committee_form = AddCommitteForm()

    # Check which form was submitted
    if 'profile_submit' in request.form:
        return handle_profile_update()
    elif 'umbrella_submit' in request.form:
        return handle_umbrella_creation(umbrella_form=umbrella_form)
    elif 'committee_submit' in request.form:
        return handle_committee_addition(committee_form=committee_form)
    elif 'block_submit' in request.form:
        return handle_block_creation(block_form=block_form)
    elif 'zone_submit' in request.form:
        return handle_zone_creation(zone_form=zone_form)
    elif 'member_submit' in request.form:
        return handle_member_creation(member_form=member_form)
    
    # Default GET request rendering the settings page
    return render_settings_page(                           
        umbrella_form=umbrella_form,block_form=block_form,zone_form=zone_form,member_form=member_form,committee_form=committee_form,
active_tab=request.args.get('active_tab', 'profile'))




def handle_profile_update():
    profile_form = ProfileForm()
    api_url = f"{current_app.config['API_BASE_URL']}/api/v1/users/{current_user.id}"

    update_data = {}
    user_changed = False

    if profile_form.validate_on_submit():
        logger.info("Form validated successfully.")

        # Handle profile picture update
        if profile_form.picture.data:
            try:
                picture_file = save_picture(profile_form.picture.data)
                image_path = os.path.join(current_app.root_path, 'static/images', picture_file)

                if current_user.image_file != picture_file:
                    with open(image_path, 'rb') as f:
                        files = {'picture': (picture_file, f, 'image/png')}
                        response = requests.patch(api_url, files=files, headers={'Authorization': f"Bearer {current_user.get_auth_token()}"})
                    
                    if response.status_code == 200:
                        flash('Profile picture updated successfully!', 'success')
                        current_user.image_file = picture_file
                        user_changed = True
                        logger.info("Profile picture updated successfully via API.")
                    else:
                        logger.error(f"Failed to update profile picture. API response: {response.status_code} - {response.text}")
                        flash('Failed to update profile picture.', 'danger')
                else:
                    flash('The new profile picture is the same as the current one.', 'info')

            except Exception as e:
                logger.error(f"Error updating profile picture: {e}")
                flash('An error occurred while updating the profile picture.', 'danger')

        # Handle other profile field updates (name, email, phone number)
        if profile_form.full_name.data != current_user.full_name:
            update_data['full_name'] = profile_form.full_name.data
            user_changed = True
        if profile_form.email.data != current_user.email:
            update_data['email'] = profile_form.email.data
            user_changed = True
        if profile_form.phone_number.data != current_user.phone_number:
            update_data['phone_number'] = profile_form.phone_number.data
            user_changed = True

        # Make API call to update profile fields if any data changed
        if update_data:
            try:
                response = requests.patch(api_url, json=update_data, headers={'Authorization': f"Bearer {current_user.get_auth_token()}"})
                if response.status_code == 200:
                    flash("Profile updated successfully!", "success")
                    logger.info("Profile fields updated successfully via API.")
                    user_changed = True
                    # Update the current user details in session after successful update
                    current_user.full_name = update_data.get('full_name', current_user.full_name)
                    current_user.email = update_data.get('email', current_user.email)
                    current_user.phone_number = update_data.get('phone_number', current_user.phone_number)
                else:
                    logger.error(f"Failed to update profile fields. API response: {response.status_code} - {response.text}")
                    errors = response.json().get('message', "An error occurred")
                    flash(errors, "danger")
            except Exception as e:
                logger.error(f"Error while updating profile fields: {e}")
                flash("An error occurred while updating profile details.", "danger")

        # Inform user if no changes were detected
        if not user_changed:
            logger.info("No changes made to profile fields or picture.")
            flash("No changes made to your profile.", "info")

    else:
        for field, errors in profile_form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "danger")

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
    

def handle_committee_addition(committee_form):

    # Retrieve the umbrella for the current user
    umbrella = get_umbrella_by_user(current_user.id)

    if not umbrella:
        flash('You need to have members before adding committee members!', 'danger')

    # Fetch blocks associated with the umbrella
    try:
        blocks = get_blocks_by_umbrella()
    except Exception as e:
        return "An error occurred while fetching data.", 500  
    
    committee_form.block_id.choices = [("", "--Choose a Block--")] + [(str(block['id']), block['name']) for block in blocks]

    if not blocks:
        flash('There are no blocks yet!', 'danger')
        return redirect(url_for('main.settings', active_tab='zone'))

    # Fetch available roles
    roles = get_roles()
    
    # Filter for Chairman (id=3), Secretary (id=4), and Treasurer (id=6)
    filtered_roles = [role for role in roles if role['id'] in [3, 4, 6]]
    
    if filtered_roles:
        committee_form.role_id.choices = [("", "--Choose a committee role--")] + [(str(role['id']), role['name']) for role in filtered_roles]

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
                return redirect(url_for('main.committee'))
            if role_id == 4 and any(role.get('id') in [3, 6] for role in user_roles):
                flash(f"{user['full_name']} has a committee role already.", 'danger')
                return redirect(url_for('main.committee'))
            if role_id == 6 and any(role.get('id') in [3, 4] for role in user_roles):
                flash(f"{user['full_name']} has a committee role already.", 'danger')
                return redirect(url_for('main.committee'))

         

            # Fetch block details and check for existing committee members
            block_response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/blocks/{block_id}")
            if block_response.status_code == 200:
                block = block_response.json()
                block_name = block['name']

                # Ensure the block doesn't already have a chairman, secretary, or treasurer
                if role_id == 3 and block.get('chairman_id'):
                    flash(f"{block_name} already has a chairman assigned.", 'danger')
                    active_tab = 'chairmen' 
                    return redirect(url_for('main.committee', active_tab=active_tab))

                if role_id == 4 and block.get('secretary_id'):
                    flash(f"{block_name} already has a secretary assigned.", 'danger')
                    active_tab = 'secretaries' 
                    return redirect(url_for('main.committee', active_tab=active_tab))

                if role_id == 6 and block.get('treasurer_id'):
                    flash(f"{block_name} already has a treasurer assigned.", 'danger')
                    active_tab = 'treasurers'
                    return redirect(url_for('main.committee', active_tab=active_tab))
            else:
                    flash(f"An error occurred while fetching the block.", 'danger')


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

    return render_settings_page(committee_form=committee_form,active_tab='committee')

def get_umbrellas():
    umbrellas_response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/umbrellas")
    return umbrellas_response.json()



# Handle umbrella creation
def handle_umbrella_creation(umbrella_form):

    if umbrella_form.validate_on_submit():
        # API call to check existing umbrella
        existing_umbrella = get_umbrella_by_user(current_user.id)
        
        if existing_umbrella:
            flash('You can only create one umbrella!', 'danger')

        # Fetch all umbrellas to check for duplicates
        umbrellas = get_umbrellas()

        # Check if the umbrella name or location already exists
        duplicate_name = any(u['name'].lower() == umbrella_form.umbrella_name.data.lower() for u in umbrellas)
        duplicate_location = any(u['location'].lower() == umbrella_form.location.data.lower() for u in umbrellas)

        # Handle duplicates
        if duplicate_name and duplicate_location:
            flash('An umbrella with this name and location already exists!', 'danger')
            return redirect(url_for('main.settings', active_tab='umbrella'))
        elif duplicate_name:
            flash('An umbrella with this name already exists!', 'danger')
            return redirect(url_for('main.settings', active_tab='umbrella'))
        elif duplicate_location:
            flash('An umbrella with this location already exists!', 'danger')
            return redirect(url_for('main.settings', active_tab='umbrella'))

        # Proceed with umbrella creation if no duplicates are found
        create_umbrella({
            'name': umbrella_form.umbrella_name.data,
            'location': umbrella_form.location.data,
            'created_by': current_user.id
        })
        flash('Umbrella created successfully!', 'success')
        return redirect(url_for('main.settings', active_tab='block'))

    return render_settings_page(umbrella_form=umbrella_form,active_tab='umbrella')

# Handle block creation using API
def handle_block_creation(block_form):
    umbrella = get_umbrella_by_user(current_user.id)

    if umbrella:
        block_form.parent_umbrella.data = umbrella['name']
    else:
        flash('You need to create an umbrella before creating a block!', 'danger')

    if block_form.validate_on_submit():
        # Check for duplicate blocks via the API
        existing_blocks = get_blocks_by_umbrella()

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

    return render_settings_page(block_form=block_form,active_tab='block')


# Handle zone creation using API
def handle_zone_creation(zone_form):
    
    # Retrieve the umbrella for the current user
    umbrella = get_umbrella_by_user(current_user.id)

    if not umbrella:
        flash('You need to create an umbrella before adding a zone!', 'danger')

    # Fetch blocks associated with the umbrella
    try:
        blocks = get_blocks_by_umbrella()
    except Exception as e:
        return "An error occurred while fetching data.", 500  
    
    zone_form.parent_block.choices = [("", "--Choose Parent Block--")] + [(str(block['id']), block['name']) for block in blocks]

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
    
    return render_settings_page(zone_form=zone_form,active_tab='zone')


# Handle member creation
def handle_member_creation(member_form):

    # Retrieve the umbrella for the current user
    umbrella = get_umbrella_by_user(current_user.id)

    if not umbrella:
        flash('You need to create an umbrella before adding a member!', 'danger')
        return redirect(url_for('main.settings', active_tab='member'))

    # Fetch blocks associated with the umbrella to populate zones
    try:
        blocks = get_blocks_by_umbrella()
    except Exception as e:
        current_app.logger.error(f"Error fetching blocks: {e}")
        return "An error occurred while fetching data.", 500  
    
    # Prepare a mapping for zones with block names
    zone_map = {}  # Store a mapping of zone_id to (zone_name, block_name)
    for block in blocks:
        # Fetch zones associated with the current block
        block_id = block['id']
        block_zones = get_zones_by_block(block_id)
        block_name = block['name']  
        for zone in block_zones:
            zone_map[zone['id']] = (zone['name'], block_name)  

    # Set the choices for the member_zone field in the form
    member_form.member_zone.choices = [("", "--Choose a Zone--")] + [(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]

    banks = get_banks()
    member_form.bank_id.choices = [("", "--Choose a Bank--")] + [(str(bank['id']), bank['name']) for bank in banks]

    if member_form.validate_on_submit():
        zone_id = member_form.member_zone.data
        existing_members = get_members_by_zone(zone_id)

        # Check if the ID number already exists in the zone
        if any(member['id_number'] == member_form.id_number.data for member in existing_members):
            flash('A member with that ID number already exists in this zone!', 'danger')
            return redirect(url_for('main.settings', active_tab='member'))

        # Check if the phone number already exists in the zone
        if any(member['phone_number'] == member_form.phone_number.data for member in existing_members):
            flash('A member with that phone number already exists in this zone!', 'danger')
            return redirect(url_for('main.settings', active_tab='member'))

        # Check if the account number already exists in the zone
        if any(member['acc_number'] == member_form.acc_number.data for member in existing_members):
            flash('A member with that account number already exists in this zone!', 'danger')
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
        response = requests.post(f"{current_app.config['API_BASE_URL']}/api/v1/users/",params={'umbrella_id': umbrella['id']}, json=payload)

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

  
    return render_settings_page(member_form=member_form,active_tab='member')



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
def get_blocks_by_umbrella():
    """Fetches blocks associated with the specified umbrella via API."""
    # Retrieve the umbrella ID for the current user
    umbrella = get_umbrella_by_user(current_user.id) 
    
    if umbrella is None or not umbrella.get('id'):
        # If no umbrella is associated, return an empty list
        print('No umbrella found.')
        return []

    umbrella_id = umbrella['id']  # Extract the umbrella ID
    
    # Make the API request to fetch blocks filtered by the parent_umbrella_id
    response = requests.get(
        f"{current_app.config['API_BASE_URL']}/api/v1/blocks/", 
        params={'parent_umbrella_id': umbrella_id}
    )

    if response.status_code == 200:
        blocks = response.json()
        return blocks
    else:
        flash('Error retrieving blocks from the server.', 'danger')
        return []


    
# Helper function to get zones of a specific block
def get_zones_by_block(block_id):
    """Fetches zones associated with the specified block via API."""
    try:
        
        response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/zones/",
            params={'parent_block_id': block_id},
            timeout=10
        )
        
        response.raise_for_status()

        zones = response.json()
        return zones
    except requests.exceptions.RequestException as e:
        print(f'Error: {e}')
        flash('Error retrieving zones from the server. Please try again later.', 'danger')
        return []
    except ValueError as e:
        flash('Error processing server response. Please contact support.', 'danger')
        return []



# Helper function to get members of a specific zone
def get_members_by_zone(zone_id):
    """Fetches members associated with the specified zone via API."""
    response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/users/", params={'zone_id': zone_id})

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
@approval_required
@roles_accepted('SuperUser', 'Administrator', 'Chairman', 'Secretary','Treasurer')
def statistics():
    
    umbrella_id = get_umbrella_by_user(current_user.id)
    print(f'fetched umbrella: {umbrella_id}')

    total_members = len(get_members())

    total_blocks = len(get_blocks_by_umbrella())

    return render_template('statistics.html', title='Statistics | Dashboard ', total_members=total_members,
        total_blocks=total_blocks, user=current_user
    )




# Helper function to render the host page with forms
def render_host_page(active_tab=None, error=None,schedule_form=None,update_form=None):

    if schedule_form is None:
        schedule_form = ScheduleForm()

    if update_form is None:
        update_form = EditMemberForm()


     # Call API or database to get upcoming meeting details
    meeting_details = get_upcoming_meeting_details()

    if meeting_details:
        meeting_block = meeting_details['meeting_block']
        meeting_zone = meeting_details['meeting_zone']
        host = meeting_details['host']
        when = meeting_details['when']
        acc_number = meeting_details['acc_number']
        paybill_no = meeting_details['paybill_no']
    else:
        meeting_block = meeting_zone = host = when = paybill_no = acc_number = None
        flash('No upcoming meetings found.','warning')
    
    message = f"""
Dear Member,
Upcoming block is hosted by {meeting_zone} and the host is {host}. Paybill: {paybill_no}, Account Number: {acc_number}."""

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
            blocks = get_blocks_by_umbrella()
            schedule_form.block.choices = [("", "--Choose a Block--")] + [(str(block['id']), block['name']) for block in blocks]
            update_form.block_id.choices =  [("", "--Choose an Additional Block--")] + [(str(block['id']), block['name']) for block in blocks]

             # Prepare a mapping for zones with block names
            zone_map = {}  # Store a mapping of zone_id to (zone_name, block_name)
            for block in blocks:
                # Fetch zones associated with the current block       
                block_id = block['id']         
                block_zones = get_zones_by_block(block_id)
                block_name = block['name']  
                for zone in block_zones:
                    zone_map[zone['id']] = (zone['name'], block_name)  # Store both zone name and block name

            # Set the choices for the member_zone field in the form
            schedule_form.zone.choices = [("", "--Choose a Zone--")] + [(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]

            update_form.member_zone.choices = [("", "--Choose an Additional Zone--")] +[(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]

            # Fetch members
            members = get_members()
            if members:
                for member in members:
                    member['bank_name'] = member.get('bank_name', 'Unknown Bank')
                    schedule_form.member.choices = [("", "--Choose a Member--")] + [(str(member['id']), member['full_name']) for member in members]
            else:
                schedule_form.member.choice = []

            banks = get_banks()
            update_form.bank_id.choices = [("", "--Choose Bank--")] + [(str(bank['id']), bank['name']) for bank in banks]

        else:
            flash('Please create an umbrella first to schedule a meeting!', 'danger')
            return redirect(url_for('main.settings',active_tab='umbrella')) 
    except Exception as e:
        logging.error(f"Error loading umbrella data: {e}", exc_info=True)


    # Render the host page
    return render_template('host.html', title='Host | Dashboard',
                           update_form=update_form,
                           user=current_user,
                           schedule_form=schedule_form,
                           blocks=blocks,message=message,
                           zones=zones,acc_number=acc_number,paybill_no=paybill_no,
                           members=members,
                           active_tab=active_tab,  
                           error=error,meeting_block=meeting_block,host=host,meeting_zone=meeting_zone,when=when)

# Single route to handle all host form submissions
@main.route('/host', methods=['GET', 'POST'])
@login_required
@approval_required
@roles_accepted('SuperUser', 'Administrator')
def host():
    schedule_form = ScheduleForm()
    update_form = EditMemberForm()
    # Check which form was submitted
    if 'schedule_submit' in request.form:
        return handle_schedule_creation(schedule_form=schedule_form)
    elif 'edit_member_submit' in request.form:  
        user_id = request.args.get('user_id')  
        return update_member(user_id, update_form=update_form)
    elif 'remove_member_submit' in request.form: 
        if request.form.get('_method') == 'DELETE':
            user_id = request.args.get('user_id')   
            return remove_member(user_id)
    elif 'send_sms' in request.form:  
        return send_sms_notifications()
        
    # Default GET request rendering the host page
    return render_host_page(schedule_form=schedule_form,update_form=update_form,active_tab=request.args.get('active_tab', 'schedule_meeting'))



# Handle schedule creation
def handle_schedule_creation(schedule_form):
     # Retrieve the umbrella for the current user
    umbrella = get_umbrella_by_user(current_user.id)

    if not umbrella:
        flash('You need to create an umbrella before scheduling a meeting!', 'danger')

    # Fetch blocks associated with the umbrella
    blocks = get_blocks_by_umbrella()
    schedule_form.block.choices = [("", "--Choose a Block--")] + [(str(block['id']), block['name']) for block in blocks]

     # Prepare a mapping for zones with block names
    zone_map = {}  # Store a mapping of zone_id to (zone_name, block_name)
    for block in blocks:
        # Fetch zones associated with the current block
        block_id = block['id']
        block_zones = get_zones_by_block(block_id)
        block_name = block['name'] 
        for zone in block_zones:
            zone_map[zone['id']] = (zone['name'], block_name)  # Store both zone name and block name

    # Set the choices for the member_zone field in the form
    schedule_form.zone.choices = [("", "--Choose a Zone--")] + [(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]

    # Fetch members filtered by zone
    members = get_members()
    if members:
        schedule_form.member.choices = [("", "--Choose a Member--")] + [(str(member['id']), member['full_name']) for member in members]



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

    return render_host_page(schedule_form=schedule_form,active_tab='schedule_meeting')



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

            # Extract the first meeting if data is a list, or use it directly if it's a dict
            first_meeting = meeting_data[0] if isinstance(meeting_data, list) and len(meeting_data) > 0 else meeting_data

            if first_meeting:
                # Parse meeting date and check if it has expired
                meeting_date_str = first_meeting.get('when', 'Unknown Date')
                try:
                    meeting_date = datetime.strptime(meeting_date_str, '%a, %d %b %Y %H:%M:%S')
                except ValueError:
                    logging.error("Invalid meeting date format received from API.")
                    return None

                if meeting_date < datetime.now():
                    logging.info("Meeting has expired; setting upcoming meeting details to None.")
                    return None

                # Extract details
                meeting_details = {
                    'meeting_block': first_meeting.get('meeting_block', 'Unknown Block'),
                    'meeting_zone': first_meeting.get('meeting_zone', 'Unknown Zone'),
                    'host': first_meeting.get('host', 'Unknown Host'),
                    'when': meeting_date_str,
                    'meeting_id': first_meeting.get('meeting_id', 'Unknown meeting ID'),
                    'paybill_no': first_meeting.get('paybill_no', 'Unknown Paybill'),
                    'acc_number': first_meeting.get('acc_number', 'Unknown Account')
                }

                logging.info(f"Extracted meeting details: {meeting_details}")
                return meeting_details
            else:
                logging.warning("No upcoming meetings found.")
                return None
        else:
            logging.error(f"Failed to fetch data from API. Status Code: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while fetching data from the API: {e}")
        return None

def send_sms_notifications():
    try:
        # Retrieve message from the form data
        message = request.form.get('message')
        print(f"Message: {message}") 
        
        # Check if any required meeting details are missing
        if message and "None" in message:
            flash('Incomplete meeting details!', 'danger')
            return redirect(url_for('main.host', active_tab='upcoming_block'))


        
        recipients = get_member_phone_numbers()
        print(f"Recipients: {recipients}") 
        if not recipients:
            flash('No recipients found for SMS notification','danger')
            return redirect(url_for('main.host', active_tab='upcoming_block'))


        # Check if the SMS service is initialized
        if sms is None:
            flash('SMS service not initialized','danger')
            return redirect(url_for('main.host', active_tab='upcoming_block'))

        # Send SMS to all recipients
        response = sms.send(
            message=message,
            recipients=recipients
            )
        print(f"SMS API Response: {response}") 
        response_data = response
        
        # Check if all recipients have a statusCode of 101
        all_successful = all(recipient['statusCode'] == 101 for recipient in response_data['SMSMessageData']['Recipients'])

        if all_successful:
            flash("Message sent successfully!", "success")
            return redirect(url_for('main.host', active_tab='upcoming_block'))
        else:
            flash("Failed to send message!", "danger")
            return redirect(url_for('main.host', active_tab='upcoming_block'))

    except Exception as e:
        flash("An unexpected error occurred!", "danger")
        current_app.logger.error(f"Failed to send notifications: {e}")
        return redirect(url_for('main.host', active_tab='upcoming_block'))
   
def get_member_phone_numbers():
    try:
        # Fetch members' details from the API
        members = get_members()  

        # Extract phone numbers, ensuring no duplicates
        phone_numbers = list({member['phone_number'] for member in members if 'phone_number' in member})
        return phone_numbers
    except Exception as e:
        current_app.logger.error(f"Error fetching phone numbers: {e}")
        return []


def update_member(user_id,update_form):

    blocks = get_blocks_by_umbrella()
    update_form.block_id.choices =  [("", "--Choose an Additional Block--")] + [(str(block['id']), block['name']) for block in blocks]

    # Prepare a mapping for zones with block names
    zone_map = {}
    for block in blocks:
        block_id = block['id']
        block_zones = get_zones_by_block(block_id)
        block_name = block['name']
        for zone in block_zones:
            zone_map[zone['id']] = (zone['name'], block_name)

    update_form.member_zone.choices =  [("", "--Choose an Additional Zone--")] + [(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]

    banks = get_banks()
    update_form.bank_id.choices = [("", "--Choose Bank--")] +  [(str(bank['id']), bank['name']) for bank in banks]

    # Fetch current user data
    try:
        current_response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/users/{user_id}")
        current_data = current_response.json() if current_response.status_code == 200 else {}
    except Exception as e:
        flash(f"Error fetching current member data: {str(e)}", "danger")
        return redirect(url_for('main.host', active_tab='block_members'))

    # Check for form submission
    if update_form.validate_on_submit():
        # Prepare payload to update member details
        payload = {}

        form_fields = {
            'full_name': 'full_name',
            'phone_number': 'phone_number',
            'id_number': 'id_number',
            'member_zone': 'zone_id',
            'bank_id': 'bank_id',
            'account_number': 'acc_number',
            'block_id': 'block_id',
        }

   
        
        # Build the payload with only changed data
        any_input = False
        for form_field, payload_key in form_fields.items():
            form_data = getattr(update_form, form_field).data
            current_value = current_data.get(payload_key)
            # If the form field has changed and it's not empty, include it in the payload
            if form_data and form_data != current_value:
                payload[payload_key] = form_data
                any_input = True

        # Check if no input was made (i.e., nothing to update)
        if not any_input and 'block_memberships' not in payload:
            flash("No input was provided. Please fill in at least one field.", "warning")
            return redirect(url_for('main.host', active_tab='block_members'))

        # Send the PATCH request to update member details
        if payload:
            try:
                response = requests.patch(f"{current_app.config['API_BASE_URL']}/api/v1/users/{user_id}", json=payload)
                if response.status_code == 200:
                    flash("Member details updated successfully.", "success")
                else:
                    flash("Failed to update member details. Please try again.", "danger")
            except Exception as e:
                flash(f"Error updating member details: {str(e)}", "danger")

        return redirect(url_for('main.host', active_tab='block_members'))

    return render_host_page(update_form=update_form,active_tab='block_members')


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
    """Fetches members associated with the specified umbrella."""
    # Retrieve the umbrella details for the current user
    umbrella = get_umbrella_by_user(current_user.id)  

    if umbrella is None or not umbrella.get('id'):
        # If no umbrella is associated, return an empty list
        print('No umbrella found.')
        return []

    umbrella_id = umbrella['id']  # Extract the umbrella ID

    try:
        logger.info("Fetching users with role 'Member' for the specified umbrella.")
        # Fetch members associated with the umbrella
        response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/users/",
            params={'role': 'Member', 'umbrella_id': umbrella_id} 
        )
        
        if response.status_code == 200:
            members = response.json()
            logger.info(f"Users fetched successfully: {len(members)} members.")
            return members
          
        else:
            logger.error(f"Error fetching members: Status Code {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Exception during fetching members: {str(e)}")
        return []


# Fetch and display committee members
def render_committee_page(active_tab=None, error=None):
    # Fetch Chairman, Secretary, and Treasurer from the API
    umbrella = get_umbrella_by_user(current_user.id)
    if not umbrella:
        flash('Please create an umbrella first to see your committee members!', 'danger')
        return redirect(url_for('main.settings', active_tab='umbrella'))

    umbrella_id = umbrella['id']  

    try:
        chairman_response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/users/", params={'role': 'Chairman','umbrella_id' : umbrella_id })
        secretary_response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/users/", params={'role': 'Secretary','umbrella_id' : umbrella_id})
        treasurer_response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/users/", params={'role': 'Treasurer','umbrella_id' : umbrella_id})

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
        print(f'Chairmen for Umbrella {umbrella_id}: {committee_members}')

        return render_template('committee.html', title='Committee | Dashboard', 
                               committee_members=committee_members, 
                               active_tab=active_tab,
                                 error=error)

    except requests.exceptions.RequestException as e:
        print(f'Committee error: {e}')
        flash(f"Error fetching committee members.", 'danger')
        return redirect(url_for('main.committee'))

# Single route to handle committee-related actions
@main.route('/committee', methods=['GET', 'POST'])
@login_required
@approval_required
@roles_accepted('SuperUser', 'Administrator')
def committee():    
    if 'remove_role_submit' in request.form:
        user_id = request.args.get('user_id')  
        active_tab = request.form.get('active_tab')  
        return remove_committee_role(user_id, active_tab)  

    return render_committee_page(active_tab=request.args.get('active_tab', 'chairmen'))


# Remove committee role (Chairman, Secretary, Treasurer)
def remove_committee_role(user_id, active_tab):
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


# Helper function to render the reports page with member contributions
def render_reports_page(active_tab=None, error=None, host_id=None, member_id=None, status=None):
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
        flash('You need to create an umbrella before getting block reports!', 'danger')
        return redirect(url_for('main.settings', active_tab='umbrella'))

    # Fetch blocks associated with the umbrella
    blocks = get_blocks_by_umbrella()
    schedule_form.block.choices = [("", "--Choose a Block--")] + [(str(block['id']), block['name']) for block in blocks]

    # Prepare a mapping for zones with block names
    zone_map = {}
    for block in blocks:
        block_id = block['id']
        block_zones = get_zones_by_block(block_id)
        block_name = block['name']
        for zone in block_zones:
            zone_map[zone['id']] = (zone['name'], block_name)

    # Set the choices for the member_zone field in the form
    schedule_form.zone.choices = [("", "--Choose a Zone--")] + [(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]

    members = []
    member_contributions = []
    combined_member_contributions = []
    host_name = 'Unknown Host'
    meeting_date = 'Unknown Date'
    block_contributions_data = {'block_contributions': []}
    try:
        # Fetch members
        members = get_members()

        # Fetch contributions for the most recent meeting
        contributions_data = get_member_contributions(host_id=host_id, member_id=member_id, status=status)
        member_contributions = contributions_data['member_contributions']
        host_name = contributions_data.get('host_name', host_name)
        meeting_date = contributions_data.get('meeting_date', meeting_date)



        # Combine member data with their contributions
        for member in members:
            contribution = next((c for c in member_contributions if c['full_name'] == member['full_name']), None)
            if contribution:
                combined_member_contributions.append({
                    'full_name': member['full_name'],
                    'amount': contribution['amount'],
                    'status': contribution.get('status', 'Unknown'),
                })
            else:
                combined_member_contributions.append({
                    'full_name': member['full_name'],
                    'amount': 0.0,
                    'status': 'Pending',
                })
        block_contributions_data = get_block_contributions(host_id=host_id)
        print(f'Block contributions: {block_contributions_data}')
        if 'block_contributions' not in block_contributions_data:
            block_contributions_data['block_contributions'] = {}


    except Exception as e:
        flash(f'Error fetching members or contributions. Please try again later.', 'danger')

    # Render the reports page
    return render_template('block_reports.html', title='Block_Reports | Dashboard',
                           user=current_user,
                           host_name=host_name,
                           meeting_date=meeting_date,
                           members=combined_member_contributions, 
                           schedule_form=schedule_form,
                        block_contributions=block_contributions_data.get('block_contributions', []),  
                           blocks=blocks,
                           active_tab=active_tab,
                           error=error)


@main.route('/block_reports', methods=['GET', 'POST'])
@login_required
@approval_required
@roles_accepted('SuperUser', 'Administrator')
def block_reports():
    host_id = request.args.get('host')
    member_id = request.args.get('member')
    status = request.args.get('status')

    
    return render_reports_page(active_tab=request.args.get('active_tab', 'block_contribution'), host_id=host_id,
        member_id=member_id,
        status=status)


def get_member_contributions(meeting_id=None, host_id=None, status=None,member_id=None):
    umbrella_id = get_umbrella_by_user(current_user.id)
    try:

        # Fetch all members of the umbrella
        members_response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/users/",
            params={'role': 'Member', 'umbrella_id': umbrella_id['id']}
        )
        
        if members_response.status_code != 200:
            flash("Error fetching members. Please try again later.", "danger")
            return []

        members = members_response.json()

        # Fetch the latest meeting if no meeting ID is provided
        if not meeting_id:
            meeting = get_upcoming_meeting_details()
            meeting_id = meeting['meeting_id']
            host_name = meeting['host']
            meeting_date = meeting['when'] 
        
        # Fetch contributions for the meeting and apply filters if provided
        contributions_params = {'meeting_id': meeting_id}
        if host_id:
            contributions_params['host_id'] = host_id
        if member_id:
            contributions_params['payer_id'] = member_id
        if status:
            contributions_params['status'] = status

        contributions_response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/payments/",
            params=contributions_params
        )

        if contributions_response.status_code != 200:
            flash("Error fetching contributions. Please try again later.", "danger")
            return []

        contributions = contributions_response.json()

        # Combine members with their contributions
        member_contributions = []
        for member in members:
            contribution_record = next((c for c in contributions if c['payer_id'] == member['id']), None)

            # Add contribution details or pending status
            if contribution_record:
                member_contributions.append({
                    'full_name': member['full_name'],
                    'amount': contribution_record['amount'],
                    'status':'Contributed' if contribution_record['transaction_status'] else 'Unknown',
                })
            else:
                member_contributions.append({
                    'full_name': member['full_name'],
                    'amount': 0.0,
                    'status': 'Pending',
                })

        return {
                    'member_contributions': member_contributions,
                    'host_name': host_name,
                    'meeting_date': meeting_date
                }

    except Exception as e:
        return []


def get_block_contributions(meeting_id=None, host_id=None):
    umbrella_id = get_umbrella_by_user(current_user.id)
    default_return = {
        'block_contributions': {}, 
        'host_name': 'Unknown Host',
        'meeting_date': 'Unknown Date'
    }
    try:
        # Fetch all blocks under the umbrella
        blocks_response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/blocks/",
            params={'umbrella_id': umbrella_id['id']}
        )

        if blocks_response.status_code != 200:
            flash("Error fetching blocks. Please try again later.", "danger")
            return []

        blocks = blocks_response.json()

        # Fetch the latest meeting if no meeting ID is provided
        if not meeting_id:
            meeting = get_upcoming_meeting_details()
            meeting_id = meeting['meeting_id']
            default_return['host_name'] = meeting['host']
            default_return['meeting_date'] = meeting['when']


        # Fetch contributions for the meeting and filter by host if provided
        contributions_params = {'meeting_id': meeting_id}
        if host_id:
            contributions_params['host_id'] = host_id

        contributions_response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/payments/",
            params=contributions_params
        )

        if contributions_response.status_code != 200:
            flash("Error fetching contributions. Please try again later.", "danger")
            return []

        contributions = contributions_response.json()

        # Aggregate contributions by block
        block_contributions = {}
        print(f'Block contributions: {block_contributions}')
        for block in blocks:
            block_contributions[block['name']] = sum(
                contribution['amount'] for contribution in contributions
                if contribution['block_id'] == block['id']
            )

        return {
            'block_contributions': block_contributions,
            'host_name': default_return['host_name'],
            'meeting_date': default_return['meeting_date']
        }

    except Exception as e:
        flash("Error fetching block contributions.", "danger")
        return []



def render_contribution_page(active_tab=None,payment_form=None, error=None):

    if payment_form is None:
        payment_form = PaymentForm()
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
        flash('Please create an umbrella first to manage contributions!', 'danger')
        return redirect(url_for('main.settings', active_tab='umbrella'))


    # Fetch blocks associated with the umbrella
    blocks = get_blocks_by_umbrella()
    payment_form.block.choices =  [("", "--Choose a Block--")] + [(str(block['id']), block['name']) for block in blocks]

    members,banks = [], []
    try:
        members = get_members()
        payment_form.member.choices =  [("", "--Choose a Member--")] + [(str(member['id']), member['full_name']) for member in members]
        banks = get_banks()
        payment_form.bank.choices =  [("", "--Choose a Bank--")] + [(str(bank['id']), bank['name']) for bank in banks]
    except Exception as e:
        print(f'payments error: {e}')
        flash(f'An error occurred. Please try again later.', 'danger')

    # Render the host page
    return render_template('manage_contribution.html', title='Manage Contribution | Dashboard',
                           user=current_user,
                           members=members,
                           payment_form=payment_form, 
                           blocks=blocks,                          
                           active_tab=active_tab, 
                           banks=banks, 
                           error=error)


@main.route('/manage_contribution', methods=['GET', 'POST'])
@login_required
@approval_required
@roles_accepted('SuperUser', 'Administrator')
def manage_contribution():
    # Get active tab
    active_tab = request.args.get('active_tab', 'request_payment')
    payment_form = PaymentForm()

    # Handle form submission
    if 'request_submit' in request.form:
        return handle_request_payment(payment_form=payment_form)
    if 'payment_submit' in request.form:
        return handle_send_to_bank(payment_form=payment_form)

    # Render the contribution page
    return render_contribution_page(payment_form=payment_form,active_tab=active_tab)


def handle_send_to_bank(payment_form):
    """
    Handles the fund transfer to the host's designated bank account
    by aggregating the member contributions and sending them to the bank.
    """
    block_id = payment_form.block.data
    bank_id = payment_form.bank.data
    acc_number = payment_form.acc_number.data
    member = payment_form.member.data

    # Populate choices for the fields before validating the form
    blocks = get_blocks_by_umbrella()
    payment_form.block.choices =  [("", "--Choose a Block--")] + [(str(block['id']), block['name']) for block in blocks]
    
    banks = get_banks()
    payment_form.bank.choices =  [("", "--Choose a Bank--")] + [(str(bank['id']), bank['name']) for bank in banks]

    members = get_members()
    payment_form.member.choices =  [("", "--Choose a Member--")] + [(str(member['id']), member['full_name']) for member in members]

    

    if payment_form.validate_on_submit():
        # Fetch total contributions for the selected block (assume an API fetch)
        try:
            response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/payments/")
            if response.status_code == 200:
                total_amount = response.json().get('total_amount')
            else:
                flash(f'Error: {response.json().get("message")}', 'danger')
                return redirect(url_for('main.manage_contribution', active_tab='send_to_bank'))
        except Exception as e:
            print(f'Total Contribution Fetch Error: {e}')
            flash('Error occurred while fetching total contributions. Please try again.', 'danger')
            return redirect(url_for('main.manage_contribution', active_tab='send_to_bank'))

        # Prepare payload for the bank transfer
        payload = {
            'block_id': block_id,
            'bank_id': bank_id,
            'acc_number': acc_number,

        }

        # Make API call to transfer funds to the bank
        try:
            response = requests.post(f"{current_app.config['API_BASE_URL']}/api/v1/payments/", json=payload)

            # Check API response
            if response.status_code == 200:
                flash('Funds transferred successfully to the bank account.', 'success')
            else:
                flash(f'Error: {response.json().get("message")}', 'danger')

        except Exception as e:
            print(f'Bank Transfer Error: {e}')
            flash('Error occurred while transferring funds. Please try again.', 'danger')

    # Redirect back to the 'Send to Bank' tab
    return render_contribution_page(payment_form=payment_form, active_tab='send_to_bank')



def handle_request_payment(payment_form):
    """
    Handles the M-Pesa payment request by sending a push notification
    to the selected member for making a contribution.
    """
    block_id = payment_form.block.data
    member_id = payment_form.member.data
    amount = payment_form.amount.data



    # Prepare payload for the API request
    payload = {
        'block_id': block_id,
        'member_id': member_id,
        'amount': amount,
    }

    # Make API call to trigger M-Pesa push notification
    try:
        response = requests.post('', json=payload)

        # Check API response
        if response.status_code == 200:
            flash('M-Pesa payment request sent successfully.', 'success')
        else:
            flash(f'Error: {response.json().get("message")}', 'danger')

    except Exception as e:
        print(f'M-Pesa Push Error: {e}')
        flash('Error occurred while processing payment request. Please try again.', 'danger')

    # Redirect back to the 'Request Payment' tab
    return render_contribution_page(payment_form=payment_form, active_tab='request_payment')
