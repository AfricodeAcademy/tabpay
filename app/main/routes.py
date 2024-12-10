from flask import Blueprint, render_template, redirect, url_for, flash,request,jsonify, session
from flask_security import login_required, current_user, roles_accepted, user_registered
from flask_wtf.csrf import  CSRFProtect
from app.main.forms import ProfileForm, AddMemberForm, AddCommitteForm, UmbrellaForm, BlockForm, ZoneForm, ScheduleForm, EditMemberForm,PaymentForm,AddMembershipForm
from app.main.models import UserModel, BlockModel, PaymentModel, ZoneModel, MeetingModel
from app.auth.decorators import approval_required, umbrella_required
from ..utils import save_picture, db

from flask import current_app
from datetime import datetime,timedelta
from ..utils.send_sms import SendSMS
from ..utils.mpesa_security import require_safaricom_ip_validation
from ..utils.mpesa import get_mpesa_client
import logging,requests,os
from functools import wraps
from ..utils.umbrella import (
    get_umbrella_by_user,
    get_blocks_by_umbrella,
    get_zones_by_block,
    cache_for_request,
)




# def exempt_from_csrf(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if request.method == 'POST':
#             validate_csrf.token = False  # Disable CSRF token validation for this route
#         return f(*args, **kwargs)
#     return decorated_function

main = Blueprint('main', __name__)
sms = SendSMS()

logger = logging.getLogger(__name__)


# def validate_ip_or_reject():
#     """Validate M-Pesa IP addresses"""
#     if not is_valid_safaricom_ip():
#         logger.warning(f"Unauthorized IP {request.remote_addr} attempted access")
#         return jsonify({
#             "ResultCode": 1,
#             "ResultDesc": "Invalid request source"
#         }), 403
#     return None

@main.route('/', methods=['GET'])
def home():
    if current_user.is_authenticated:
        # Check for SuperUser role first
        if current_user.has_role('SuperUser'):
            return redirect(url_for('admin.index'))
        
        # Check for other administrative roles
        admin_roles = ['Administrator', 'Chairman', 'Secretary', 'Treasurer']
        if current_user.is_approved and any(current_user.has_role(role) for role in admin_roles):
            return redirect(url_for('main.statistics'))
            
        # For regular members or other roles, redirect to contribution page
        if current_user.has_role('Member'):
            return redirect(url_for('main.render_contribution_page'))
            
    # Only unauthenticated users or users without specific roles can see the landing page
    return render_template('index.html')

@main.errorhandler(403)
def forbidden_error(error):
    flash('You must log in to access this page.', 'warning')
    return redirect(url_for('security.login'))


# Helper function to render the settings page with forms
def render_settings_page(umbrella_form=None, block_form=None, zone_form=None,
                        member_form=None, committee_form=None, active_tab='profile',
                        selected_block='', selected_zone=''):
    """Helper function to render settings page with all necessary forms and data"""
    blocks = get_blocks_by_umbrella()
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
            
            # Pre-populate committee form choices
        blocks = get_blocks_by_umbrella()
        roles = get_roles()
            
        if blocks and isinstance(blocks, list):
            committee_form.block_id.choices = [("", "Choose a Block")] + [(str(block['id']), block['name']) for block in blocks]
            
        if roles and isinstance(roles, list):
            committee_form.role_id.choices = [("", "Choose a Committee Role")] + [(str(role['id']), role['name']) for role in roles]

  # API call to get user details
    try:
        user = get_user_from_api(current_user.id)
        if user:
            # Autofill form fields with user data
            profile_form.full_name.data = user.get('full_name', '')
            profile_form.email.data = user.get('email', '')
        else:
            flash('Unable to load user data.', 'danger')
    except Exception as e:
        flash('Error loading user details. Please try again later.', 'danger')
    
    umbrella = get_umbrella_by_user(current_user.id)

    if not umbrella:
        flash('You need to create an umbrella before adding a member!', 'danger')
        return redirect(url_for('main.settings', active_tab='umbrella'))

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
        block_name = block['name']  #_idlock name from the block data
        for zone in block_zones:
            zone_map[zone['id']] = (zone['name'], block_name)  # Store both zone name and block name
            
    member_form.umbrella.data = umbrella['name']
    # member_form.member_block.choices = [("", "--Choose a Block--")] + [(str(block['id']), block['name']) for block in blocks]

    # Set the choices for the member_zone field in the form
    member_form.member_zone.choices = [("", "--Choose a Zone--")] + [(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]
    # member_form.member_block.choices = [("", "--Choose a Block--")] + [(str(block['id']), block['name']) for block in blocks]

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
                           zones=zone_map.keys(),  
                           active_tab=active_tab,  
                           selected_block=selected_block,
                           selected_zone=selected_zone)

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
        return handle_block_creation(block_form=block_form)
    elif 'zone_submit' in request.form:
        return handle_zone_creation(zone_form=zone_form)
    elif 'member_submit' in request.form:
        try:
            # For Cascade dropdown - AJAX
            # Get the block_id from the form data
            block_id = request.form.get('block')
            zone_id = member_form.member_zone.data
            
            # Store in session
            session['selected_block'] = block_id
            session['selected_zone'] = zone_id
            
            return handle_member_creation(member_form=member_form)
        except Exception as e:
            flash(f'Error adding member: {str(e)}', 'danger')
    # For Cascade dropdown - AJAX 
    # Default GET request rendering the settings page
    # Get stored values from session
    selected_block = session.get('selected_block', '')
    selected_zone = session.get('selected_zone', '')
    
    return render_settings_page(
    #For Cascade dropdown - AJAX                           
        umbrella_form=umbrella_form,block_form=block_form,zone_form=zone_form,member_form=member_form,committee_form=committee_form,
active_tab=request.args.get('active_tab', 'profile'), selected_block=selected_block, selected_zone=selected_zone)



def handle_profile_update():
    profile_form = ProfileForm()
    api_url = f"{current_app.config['API_BASE_URL']}/api/v1/users/{current_user.id}"

    update_data = {}
    user_changed = False

    if profile_form.validate_on_submit():

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
                    else:
                        flash('Failed to update profile picture.', 'danger')
                else:
                    flash('The new profile picture is the same as the current one.', 'info')

            except Exception as e:
                flash('An error occurred while updating the profile picture.', 'danger')

        # Handle other profile field updates (name, email, phone number)
        if profile_form.full_name.data != current_user.full_name:
            update_data['full_name'] = profile_form.full_name.data
            user_changed = True
        if profile_form.email.data != current_user.email:
            update_data['email'] = profile_form.email.data
            user_changed = True
   

        # Make API call to update profile fields if any data changed
        if update_data:
            try:
                response = requests.patch(api_url, json=update_data, headers={'Authorization': f"Bearer {current_user.get_auth_token()}"})
                if response.status_code == 200:
                    flash("Profile updated successfully!", "success")
                    user_changed = True
                    # Update the current user details in session after successful update
                    current_user.full_name = update_data.get('full_name', current_user.full_name)
                    current_user.email = update_data.get('email', current_user.email)
                else:
                    errors = response.json().get('message', "An error occurred")
                    flash(errors, "danger")
            except Exception as e:
                flash("An error occurred while updating profile details.", "danger")

        # Inform user if no changes were detected
        if not user_changed:
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
        # current_app.logger.debug(f"API Response: {response.json()}")  
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
                    flash(f"{block_name} already has a chairperson assigned.", 'danger')
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
            zone_map[zone['id']] = (zone['name'], block_name)  # Store both zone name and block name

    member_form.umbrella.data = umbrella['name']

    # Set the choices for the member_zone field in the form
    member_form.member_zone.choices = [("", "--Choose a Zone--")] + [(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]
    # member_form.member_block.choices = [("", "--Choose a Block--")] + [(str(block['id']), block['name']) for block in blocks]

    banks = get_banks()
    member_form.bank_id.choices = [("", "--Choose a Bank--")] + [(str(bank['id']), bank['name']) for bank in banks]


    errors = member_form.errors
    print(errors)

    if member_form.validate_on_submit():
        print(member_form.data)  # Log submitted data
        zone_id = member_form.member_zone.data
        existing_members = get_members_by_zone(zone_id,umbrella['id'])

        # Custom validation logic
        if any(member['id_number'] == member_form.id_number.data for member in existing_members):
            member_form.id_number.errors.append('A member with that ID number already exists ')

        if any(member['phone_number'] == member_form.phone_number.data for member in existing_members):
            member_form.phone_number.errors.append('A member with that phone number already exists')

        if any(member['acc_number'] == member_form.acc_number.data for member in existing_members):
            member_form.acc_number.errors.append('A member with that account number already exists ')

        # If any errors exist, re-render the form with errors
        if member_form.errors:
            return render_settings_page(member_form=member_form, active_tab='member')

   
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
            error_message = response.json().get('message', 'Unknown error')
            print(error_message)
            flash('Failed to create member.', 'danger')
        
        # Persist zone selection for convenience
        return redirect(url_for('main.settings', active_tab='member', zone_id=member_form.member_zone.data))
    
    print(member_form.errors)  # Log validation errors


  
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
    

# Helper function to get members of a specific zone
def get_members_by_zone(zone_id,umbrella_id):
    """Fetches members associated with the specified zone via API."""
    response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/users/", params={'role':'Member','zone_id': zone_id,'umbrella_id': umbrella_id})

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
@roles_accepted('SuperUser', 'Administrator', 'Chairman', 'Secretary', 'Treasurer')
def statistics():
    # Fetch all members
    all_members = get_members() 

    try:
        # Fetch all meetings to identify hosts
        response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/meetings/")
        if response.status_code == 200:
            meetings = response.json()  
        elif response.status_code == 404:  # No meetings found
            meetings = []
        else:
            print("Failed to fetch meetings data from the API.")
            meetings = []

    except Exception as e:
        print(f"Error fetching meetings data: {e}")
        flash("An error occurred while retrieving meetings data.", "danger")
        meetings = []

    # Extract the IDs of members who have hosted
    hosted_member_ids = {meeting['host_id'] for meeting in meetings}

    # Identify members who haven't hosted
    yet_to_host = [member for member in all_members if member['id'] not in hosted_member_ids]

    total_members = len(all_members)
    total_blocks = len(get_blocks_by_umbrella())

    return render_template(
        'statistics.html',
        title='Statistics | Dashboard',
        total_members=total_members,
        total_blocks=total_blocks,
        yet_to_host=len(yet_to_host),
        user=current_user
    )




# Helper function to render the host page with forms
def render_host_page(active_tab=None, error=None,schedule_form=None,update_form=None,add_membership_form=None):

    if schedule_form is None:
        schedule_form = ScheduleForm()

    if update_form is None:
        update_form = EditMemberForm()
    
    if add_membership_form is None:
        add_membership_form = AddMembershipForm()


     # Call API or database to get upcoming meeting details
    meeting_details = get_upcoming_meeting_details()

    if meeting_details:
        meeting_block = meeting_details['meeting_block']
        meeting_zone = meeting_details['meeting_zone']
        host = meeting_details['host']
        when = meeting_details['when']
        acc_number = meeting_details['acc_number']
        paybill_no = meeting_details['paybill_no']
        event_id = meeting_details['event_id']
        meeting_id = meeting_details['meeting_id']
    else:
        meeting_block = meeting_zone = host = when = paybill_no = acc_number = event_id = meeting_id = None
        flash('No meetings scheduled for this week. Use the "Schedule Meeting" tab to create one.', 'info')
    
    message = (
    f"Dear Member, \n"
    f"Upcoming block is hosted by {meeting_zone} and the host is {host}. \n"
    f"Paybill: 4145819, Account Number: {event_id}. \n"
    f"When: {when}"
).strip()
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
    schedule_form.block.choices = [("", "--Choose a Block--")] + [(str(block['id']), block['name']) for block in blocks]
    update_form.block_id.choices =  [(str(block['id']), block['name']) for block in blocks]

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

    update_form.member_zone.choices = [(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]
    # Get current page from request arguments (default is page 1)

    current_page = int(request.args.get('page', 1))
    members_per_page = 5  # Number of members per page
    # Fetch members
    members = get_members()
    if members:
        for member in members:
            member['bank_name'] = member.get('bank_name', 'Unknown Bank')
            schedule_form.member.choices = [("", "--Choose a Member--")] + [(str(member['id']), member['full_name']) for member in members]
    else:
        schedule_form.member.choice = []
    total_pages = 1  # Initialize with default value
    total_members = len(members)
    total_pages = (total_members + members_per_page - 1) // members_per_page
    # Apply slicing for pagination
    start = (current_page - 1) * members_per_page
    end = start + members_per_page
    paginated_members = members[start:end]

    # Prepare pagination metadata
    pagination = {
        "current_page": current_page,
        "total_pages": total_pages,
        "has_prev": current_page > 1,
        "has_next": current_page < total_pages
    }


    banks = get_banks()
    update_form.bank_id.choices = [(str(bank['id']), bank['name']) for bank in banks]

    # Render the host page
    return render_template('host.html', title='Host | Dashboard',
                           update_form=update_form,add_membership_form=add_membership_form,
                           user=current_user,
                            meeting_id=(meeting_details or {}).get('meeting_id', ''),
                           schedule_form=schedule_form,
                           blocks=blocks,message=message,
                           zones=zone_map.keys(),acc_number=acc_number,paybill_no=paybill_no,
                            members=paginated_members,
                            pagination=pagination,
                           active_tab=active_tab,  
                           error=error,meeting_block=meeting_block,host=host,meeting_zone=meeting_zone,when=when,event_id=event_id)

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
    elif 'edit_meeting' in request.form:  
        meeting_id = request.args.get('meeting_id')  
        print(f"MEETING ID FROM REQUEST ARGS: {meeting_id}")
        return edit_meeting_details(meeting_id, schedule_form=schedule_form)
    elif 'remove_member_submit' in request.form: 
        if request.form.get('_method') == 'DELETE':
            user_id = request.args.get('user_id')   
            return remove_member(user_id)
    elif 'send_sms' in request.form:  
        return send_sms_notifications()
    add_membership_form = AddMembershipForm()
    # Fetch blocks associated with the umbrella
    blocks = get_blocks_by_umbrella()
    add_membership_form.block.choices = [("", "--Choose a Block--")] + [(str(block['id']), block['name']) for block in blocks]

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
    add_membership_form.zone.choices = [("", "--Choose a Zone--")] + [(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]


    if request.method == 'POST' and 'add_membership_submit' in request.form:
        if add_membership_form.validate_on_submit():
            id_number = add_membership_form.id_number.data
            block_id = add_membership_form.block.data
            zone_id = add_membership_form.zone.data
            payload = {
                    "block_id": block_id,
                    "zone_id": zone_id
                }
            
        user = get_user_by_id_number(id_number)
        user_id = user['id']
        # API call to add membership
        try:
            response = requests.patch(
                f"{current_app.config['API_BASE_URL']}/api/v1/users/{user_id}",
                json=payload,
            )
            if response.status_code == 200:
                flash("Membership added successfully!", "success")
            else:
                flash(response.json().get('message', 'Failed to add membership'), "danger")
        except Exception as e:
            flash(f"Error updating member details: {str(e)}", "danger")      

        return redirect(url_for('main.host', active_tab='block_members'))
        
    # Default GET request rendering the host page
    return render_host_page(schedule_form=schedule_form,add_membership_form=add_membership_form,update_form=update_form,active_tab=request.args.get('active_tab', 'schedule_meeting'))


def edit_meeting_details(meeting_id, schedule_form):
    # Fetch current meeting data
    try:
        current_response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/meetings/{meeting_id}")
        if current_response.status_code == 200:
            current_data = current_response.json()
        else:
            current_data = {}
    except Exception as e:
        print(f"Error fetching meeting data: {str(e)}")
        flash("Error fetching meeting data.", "danger")
        return redirect(url_for('main.host', active_tab='upcoming_block'))

    if schedule_form.validate_on_submit():
        # Collect only the form data fields that are provided
        payload = {}

        form_fields = {
            'host': 'host',
            'when': 'when',
            'zone_id': 'zone_id',
            'block_id': 'block_id',
        }
        
        any_input = False
        for form_field, payload_key in form_fields.items():
            form_data = getattr(schedule_form, form_field).data
            current_value = current_data.get(payload_key)

            # Special handling for the 'when' (date) field
            if form_field == 'when':
                if form_data:
                    try:       

                        # Convert form data into a datetime object
                        formatted_date = datetime.strptime(form_data, '%Y-%m-%d %H:%M:%S')
                        if formatted_date != datetime.fromisoformat(current_value):  # Compare with current value
                            payload[payload_key] = formatted_date.isoformat()  # Ensure ISO 8601 format
                            any_input = True
                    except ValueError:
                        flash("Invalid date format. Please use YYYY-MM-DDTHH:MM:SS.", "danger")
                        return redirect(url_for('main.host', active_tab='upcoming_block'))
            else:
                # If the form field has changed and it's not empty, include it in the payload
                if form_data and form_data != current_value:
                    payload[payload_key] = form_data
                    any_input = True

        # Check if no input was made (i.e., nothing to update)
        if not any_input:
            flash("No changes made.", "warning")
            return redirect(url_for('main.host', active_tab='upcoming_block'))

        # Call the API to update the meeting with partial data
        success = update_meeting_api(meeting_id, payload)

        if success:
            flash("Meeting details updated successfully.", "success")
        else:
            flash("Failed to update meeting details.", "danger")
    else:
        # Debugging validation issues
        print(schedule_form.errors)
        flash("Invalid form data.", "danger")
        return redirect(url_for('main.host', active_tab='upcoming_block'))

    return redirect(url_for('main.host', active_tab='upcoming_block'))


def update_meeting_api(meeting_id, payload):
    try:
        response = requests.patch(
            f"{current_app.config['API_BASE_URL']}/api/v1/meetings/{meeting_id}",
            json=payload
        )
        print(f"DETAILS FOR UPDATING THE MEEETING: {    response.json()}")
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Failed to update meeting: {e}")
        return False




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
            print(f"Attempting to schedule meeting with payload: {payload}")
            response = requests.post(f"{current_app.config['API_BASE_URL']}/api/v1/meetings/", json=payload)
            print(f"API Response Status: {response.status_code}")
            print(f"API Response Content: {response.text}")
            if response.status_code == 201:
                flash("Meeting has been scheduled successfully!", "success")
                return redirect(url_for('main.host', active_tab='schedule_meeting'))
            else:
                error_msg = response.json().get('error', 'Meeting scheduling failed. Please try again later.')
                flash(error_msg, 'danger')
        except Exception as e:
            print(f"Meeting scheduling error: {e}")
            flash('Error creating meeting. Please try again later.', 'danger') 

    return render_host_page(schedule_form=schedule_form,active_tab='schedule_meeting')


def get_upcoming_meeting_details():
    """Fetch upcoming meetings for the current user.
    
    Returns:
        dict: Meeting details if found, None otherwise
    """
    today = datetime.now()
    week_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = (week_start + timedelta(days=6)).replace(hour=23, minute=59, second=59)

    organizer_id = current_user.id

    try:
        # Get user's umbrella first
        umbrella = get_umbrella_by_user(current_user.id)
        if not umbrella:
            logging.warning(f"No umbrella found for user {organizer_id}")
            return None

        logging.info(f"Fetching upcoming meetings for organizer_id={organizer_id}, umbrella_id={umbrella.get('id')}, start={week_start}, end={week_end}")

        # Format dates in ISO format for API
        params = {
            'start_date': week_start.isoformat(),
            'end_date': week_end.isoformat(),
            'organizer_id': organizer_id,
            'umbrella_id': umbrella.get('id')
        }

        response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/meetings/",
            params=params,
            headers={
                "Authorization": f"Bearer {current_user.get_auth_token()}",
                "Content-Type": "application/json"
            },
            timeout=20
        )
        
        # Log the full request details for debugging
        logging.info(f"API request URL: {response.request.url}")
        logging.info(f"API request headers: {response.request.headers}")
        logging.info(f"API response status: {response.status_code}")

        if response.status_code == 200:
            meeting_data = response.json()
            logging.info(f"API response received: {meeting_data}")

            # Handle empty response
            if not meeting_data:
                logging.info("No meetings found in response")
                return None

            # Extract the first meeting if data is a list
            first_meeting = meeting_data[0] if isinstance(meeting_data, list) else meeting_data

            if not first_meeting:
                logging.info("No valid meeting data found")
                return None

            # Parse meeting date and check if it has expired
            meeting_date_str = first_meeting.get('when')
            if not meeting_date_str:
                logging.error("Meeting date not found in response")
                return None

            try:
                # Try multiple date formats
                for date_format in ['%a, %d %b %Y %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                    try:
                        meeting_date = datetime.strptime(meeting_date_str, date_format)
                        break
                    except ValueError:
                        continue
                else:
                    logging.error(f"Could not parse meeting date: {meeting_date_str}")
                    return None

                # Compare dates using date components only for expiration check
                today = datetime.now().date()
                meeting_date_only = meeting_date.date()
                
                if meeting_date_only < today:
                    logging.info(f"Meeting has expired. Meeting date: {meeting_date_only}, Today: {today}")
                    return None

                # Extract details with proper validation
                meeting_details = {
                    'meeting_block': first_meeting.get('meeting_block', 'Unknown Block'),
                    'meeting_zone': first_meeting.get('meeting_zone', 'Unknown Zone'),
                    'host': first_meeting.get('host', 'Unknown Host'),
                    'meeting_id': first_meeting.get('meeting_id'),
                    'when': meeting_date_str,
                    'event_id': first_meeting.get('event_id'),
                    'paybill_no': first_meeting.get('paybill_no'),
                    'acc_number': first_meeting.get('acc_number')
                }

                # Validate required fields
                required_fields = ['meeting_id', 'event_id', 'paybill_no', 'acc_number']
                if any(not meeting_details.get(field) for field in required_fields):
                    logging.error(f"Missing required fields in meeting data: {meeting_details}")
                    return None

                logging.info(f"Successfully extracted meeting details: {meeting_details}")
                return meeting_details

            except Exception as e:
                logging.error(f"Error processing meeting date: {str(e)}")
                return None

        elif response.status_code == 404:
            logging.info("No meetings found for the specified criteria")
            return None
        else:
            logging.error(f"API request failed with status {response.status_code}")
            try:
                error_data = response.json()
                logging.error(f"API error response: {error_data}")
            except:
                logging.error(f"Raw API error response: {response.text}")
            return None

    except requests.exceptions.Timeout:
        logging.error("API request timed out after 20 seconds")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"API request error: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
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
        
        # Check if response is None
        if response is None:
            flash("Message sent successfully!", "success")
            return redirect(url_for('main.host', active_tab='upcoming_block'))
            
        response_data = response
        print(f"SMS API Response Data: {response_data}") 
        
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


def update_member(user_id, update_form):
    # Fetch blocks, zones, and banks
    blocks = get_blocks_by_umbrella()
    update_form.block_id.choices = [("", "--Choose an Additional Block--")] + [(str(block['id']), block['name']) for block in blocks]

    umbrella = get_umbrella_by_user(current_user.id)
    zone_map = {}
    for block in blocks:
        block_id = block['id']
        block_zones = get_zones_by_block(block_id)
        block_name = block['name']
        for zone in block_zones:
            zone_map[zone['id']] = (zone['name'], block_name)  # Store both zone name and block name

    update_form.member_zone.choices = [("", "--Choose an Additional Zone--")] + [
        (str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()
    ]

    banks = get_banks()
    update_form.bank_id.choices = [("", "--Choose Bank--")] + [(str(bank['id']), bank['name']) for bank in banks]

    # Fetch current user data
    try:
        current_response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/users/{user_id}")
        current_data = current_response.json() if current_response.status_code == 200 else {}
    except Exception as e:
        flash(f"Error fetching current member data: {str(e)}", "danger")
        return redirect(url_for('main.host', active_tab='block_members'))

    # Fetch all members to check for uniqueness
    try:
        members_response = requests.get(f"{current_app.config['API_BASE_URL']}/api/v1/users", params={'umbrella_id': current_data['umbrella_id']})
        members = members_response.json() if members_response.status_code == 200 else []
    except Exception as e:
        flash(f"Error fetching members for uniqueness check: {str(e)}", "danger")
        return render_host_page(update_form=update_form, active_tab='block_members')

    # Check for form submission
    if update_form.validate_on_submit():
        payload = {}
        any_input = False

        # Validate uniqueness of phone number, ID number, and account number
        unique_fields = ['id_number', 'phone_number', 'account_number']
        for field in unique_fields:
            form_data = getattr(update_form, field).data
            current_value = current_data.get(field)

            # Check uniqueness in the member list
            for member in members:
                if member.get(field) == form_data and member['id'] != user_id:
                    flash(f"{field.replace('_', ' ').title()} is already in use by another member.", "danger")
                    return render_host_page(update_form=update_form, active_tab='block_members')

            payload[field] = form_data
            any_input = True

        # Include other fields if they are changed
        other_fields = {
            'full_name': 'full_name',
            'member_zone': 'zone_id',
            'bank_id': 'bank_id',
            'block_id': 'block_id',
        }

        for form_field, payload_key in other_fields.items():
            form_data = getattr(update_form, form_field).data
            current_value = current_data.get(payload_key)
            if form_data and form_data != current_value:
                payload[payload_key] = form_data
                any_input = True

        if not any_input:
            flash("No input was provided. Please fill in at least one field.", "warning")
            return redirect(url_for('main.host', active_tab='block_members'))

        # Send patch request
        try:
            response = requests.patch(
                f"{current_app.config['API_BASE_URL']}/api/v1/users/{user_id}",
                json=payload,
                params={'umbrella_id': current_data['umbrella_id']}
            )
            if response.status_code == 200:
                flash("Member details updated successfully.", "success")
            else:
                flash("Failed to update member details. Please try again.", "danger")
        except Exception as e:
            flash(f"Error updating member details: {str(e)}", "danger")

        return redirect(url_for('main.host', active_tab='block_members'))

    return render_host_page(update_form=update_form, active_tab='block_members')



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
def get_members(page=1, per_page=5):
    """Fetches members associated with the specified umbrella."""
    # Retrieve the umbrella details for the current user
    umbrella = get_umbrella_by_user(current_user.id)  
    
    if umbrella is None or not umbrella.get('id'):
        # If no umbrella is associated, return an empty list
        print('No umbrella found.')
        return []

    umbrella_id = umbrella['id']  # Extract the umbrella ID

    try:
        # Fetch members associated with the umbrella
        response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/users/",
            params={'role': 'Member', 'umbrella_id': umbrella_id,"page": page, "per_page": per_page} 
        )
        
        if response.status_code == 200:
            members = response.json()
            return members
          
        else:
            return []
    except Exception as e:
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
        flash(f"Error removing committee role!", 'danger')
        return redirect(url_for('main.committee', active_tab=active_tab))


# Helper function to render the reports page with member contributions
def render_reports_page(active_tab=None, error=None, host_id=None, member_id=None, status=None, umbrella=None):
    schedule_form = ScheduleForm()
    total_pages = 1  # Initialize with default value
    
    # Initialize variables that might be used in template
    meeting_block = None
    host = None
    meeting_zone = None
    when = None
    event_id = None
    
    umbrella = get_umbrella_by_user(current_user.id)

    if not umbrella:
        flash('You need to create an umbrella before getting block reports!', 'danger')
        return redirect(url_for('main.settings', active_tab='umbrella'))

    # Fetch blocks and populate form choices
    blocks = get_blocks_by_umbrella()
    schedule_form.block.choices = [("", "--Choose a Block--")] + [(str(block['id']), block['name']) for block in blocks]

    # Mapping zones to blocks
    zone_map = {}
    for block in blocks:
        block_id = block['id']
        block_zones = get_zones_by_block(block_id)
        block_name = block['name']
        for zone in block_zones:
            zone_map[zone['id']] = (zone['name'], block_name)  # Store both zone name and block name

    schedule_form.zone.choices = [("", "--Choose a Zone--")] + [(str(zone_id), f"{zone_name} - ({block_name})") for zone_id, (zone_name, block_name) in zone_map.items()]

    current_page = int(request.args.get('page', 1))
    members_per_page = 5  # Number of members per page

    combined_member_contributions = []
    host_name = 'No hosting scheduled'
    meeting_date = ''
    block_contributions_data = {'block_contributions': []}

    try:
        # Fetch all members and contributions
        all_members = get_members()
        contributions_data = get_member_contributions(host_id=host_id, member_id=member_id, status=status)
        member_contributions = contributions_data['member_contributions']
        host_name = contributions_data.get('host_name', host_name)
        meeting_date = contributions_data.get('meeting_date', meeting_date)

        # Slice members for pagination
        total_members = len(all_members)
        total_pages = (total_members + members_per_page - 1) // members_per_page
        start = (current_page - 1) * members_per_page
        end = start + members_per_page
        paginated_members = all_members[start:end]

        # Combine paginated members with their contributions
        for member in paginated_members:
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

        # Fetch block contributions
        block_contributions_data = get_block_contributions(host_id=host_id)

    except Exception as e:
        print(f"Error fetching members or contributions: {e}")
        flash('Error fetching data. Please try again later.', 'danger')

    # Pagination metadata
    pagination = {
        "current_page": current_page,
        "total_pages": total_pages,
        "has_prev": current_page > 1,
        "has_next": current_page < total_pages,
    }

    # Render the reports page
    return render_template('block_reports.html',
                           title='Block Reports | Dashboard',
                           user=current_user,
                           host_name=host_name,
                           meeting_date=meeting_date,
                           members=combined_member_contributions,
                           pagination=pagination,
                           schedule_form=schedule_form,
                           block_contributions=block_contributions_data.get('block_contributions', []),
                           blocks=blocks,
                           active_tab=active_tab,  
                           error=error,meeting_block=meeting_block,host=host,meeting_zone=meeting_zone,when=when,event_id=event_id)

@main.route('/block_reports', methods=['GET'])
@login_required
@umbrella_required
def block_reports(umbrella):
    host_id = request.args.get('host_id')
    member_id = request.args.get('member_id')
    status = request.args.get('status')
    return render_reports_page(active_tab=request.args.get('active_tab', 'block_contribution'), 
                             host_id=host_id,
                             member_id=member_id,
                             status=status,
                             umbrella=umbrella)

def get_block_contributions(meeting_id=None, host_id=None):
    # Get the current user's umbrella
    umbrella = get_umbrella_by_user(current_user.id)
    if not umbrella:
        flash('You need to create an umbrella before getting block reports!', 'danger')
        return {
            'block_contributions': {}, 
            'host_name': 'Unknown Host',
            'meeting_date': 'Unknown Date'
        }

    try:
        # Fetch all blocks under the umbrella
        blocks_response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/blocks/", 
            params={'parent_umbrella_id': umbrella['id']}  # Use parent_umbrella_id instead of umbrella_id
        )

        if blocks_response.status_code != 200:
            flash("Error fetching blocks. Please try again later.", "danger")
            return []

        blocks = blocks_response.json()

        # Fetch the latest meeting if no meeting ID is provided
        if not meeting_id:
            meeting = get_upcoming_meeting_details()
            if not meeting:
                return {
                    'block_contributions': {},
                    'host_name': 'Unknown Host',
                    'meeting_date': 'Unknown Date'
                }
            meeting_id = meeting.get('meeting_id')
            host_name = meeting.get('host', 'Unknown Host')
            meeting_date = meeting.get('when', 'Unknown Date')
        else:
            # Verify that the meeting belongs to the umbrella's blocks
            meeting_response = requests.get(
                f"{current_app.config['API_BASE_URL']}/api/v1/meetings/{meeting_id}"
            )
            if meeting_response.status_code != 200:
                flash("Error fetching meeting details.", "danger")
                return []
            
            meeting_data = meeting_response.json()
            block_id = meeting_data.get('block_id')
            # Check if the block belongs to the umbrella
            if not any(block['id'] == block_id for block in blocks):
                flash("You do not have permission to view this meeting's contributions.", "danger")
                return []
            host_name = meeting_data.get('host_name', 'Unknown Host')
            meeting_date = meeting_data.get('date', 'Unknown Date')

        # Fetch contributions for the meeting and filter by host if provided
        contributions_params = {'meeting_id': meeting_id}
        if host_id:
            # Verify that the host belongs to the umbrella's blocks
            host_response = requests.get(
                f"{current_app.config['API_BASE_URL']}/api/v1/users/{host_id}"
            )
            if host_response.status_code != 200:
                flash("Error fetching host details.", "danger")
                return []
            
            host_data = host_response.json()
            host_blocks = host_data.get('block_memberships', [])
            if not any(block['parent_umbrella_id'] == umbrella['id'] for block in host_blocks):
                flash("You do not have permission to view this host's contributions.", "danger")
                return []
            
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
        for block in blocks:
            block_contributions[block['name']] = sum(
                contribution['amount'] for contribution in contributions
                if contribution['block_id'] == block['id']
            )

        return {
            'block_contributions': block_contributions,
            'host_name': host_name,
            'meeting_date': meeting_date
        }

    except Exception as e:
        flash("Error fetching block contributions.", "danger")
        return []


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

    # Get member details
    try:
        member = next((m for m in get_members() if str(m['id']) == str(member_id)), None)
        if not member:
            flash('Member not found.', 'danger')
            return render_contribution_page(payment_form=payment_form, active_tab='request_payment')

        # Extract phone number from member details
        phone_number = member.get('phone_number')
        if not phone_number:
            flash('Member phone number not found.', 'danger')
            return render_contribution_page(payment_form=payment_form, active_tab='request_payment')

        # Get the block to find its umbrella
        block = BlockModel.query.get(block_id)
        if not block:
            flash('Block not found.', 'danger')
            return render_contribution_page(payment_form=payment_form, active_tab='request_payment')

        # Get the active umbrella meeting
        now = datetime.now()
        logger.info(f"Searching for meeting in block {block_id} with umbrella {block.parent_umbrella_id}")
        
        # First try to find a meeting that started within the last 24 hours
        umbrella_meeting = MeetingModel.query.join(BlockModel).filter(
            BlockModel.parent_umbrella_id == block.parent_umbrella_id,
            MeetingModel.date >= now - timedelta(hours=24)  # Meeting started within last 24 hours
        ).order_by(MeetingModel.date.desc()).first()
        
        if umbrella_meeting:
            logger.info(f"Found recent meeting: ID={umbrella_meeting.id}, Date={umbrella_meeting.date}, Unique_ID={umbrella_meeting.unique_id}")
        else:
            logger.info("No recent meeting found, looking for latest scheduled meeting")
            # If no recent meeting, try to find the latest scheduled meeting
            umbrella_meeting = MeetingModel.query.join(BlockModel).filter(
                BlockModel.parent_umbrella_id == block.parent_umbrella_id
            ).order_by(MeetingModel.date.desc()).first()
            
            if umbrella_meeting:
                logger.info(f"Found latest meeting: ID={umbrella_meeting.id}, Date={umbrella_meeting.date}, Unique_ID={umbrella_meeting.unique_id}")
            else:
                logger.error(f"No meeting found for umbrella {block.parent_umbrella_id}")
                
        if not umbrella_meeting:
            flash('No active meeting found. Please ensure there is a scheduled meeting.', 'danger')
            return render_contribution_page(payment_form=payment_form, active_tab='request_payment')
            
        logger.info(f"Found meeting: ID={umbrella_meeting.id}, Date={umbrella_meeting.date}, Unique_ID={umbrella_meeting.unique_id}")
        
        # Use the umbrella meeting's unique_id as the bill reference (this matches the account number in SMS)
        bill_ref = umbrella_meeting.unique_id

        # Initialize M-Pesa payment using the umbrella meeting's unique_id
        try:
            mpesa = get_mpesa_client()
            response = mpesa.initiate_payment(
                amount=int(amount),
                phone_number=phone_number,
                bill_ref_number=bill_ref  # This matches the account number sent in SMS
            )

            # Log successful payment initiation
            logger.info(f"M-Pesa payment initiated for umbrella meeting {bill_ref}: {response}")
            flash('M-Pesa payment request sent successfully.', 'success')

        except Exception as e:
            logger.error(f'M-Pesa payment error for umbrella meeting {bill_ref}: {str(e)}')
            flash('Error occurred while processing payment request. Please try again.', 'danger')

    except Exception as e:
        logger.error(f'Error fetching member details: {str(e)}')
        flash('Error occurred while processing payment request. Please try again.', 'danger')

    # Redirect back to the 'Request Payment' tab
    return render_contribution_page(payment_form=payment_form, active_tab='request_payment')

@main.route('/payments/confirmation', methods=['POST'])
@require_safaricom_ip_validation
def mpesa_confirmation():
    print(request.json)
    """Handle M-Pesa confirmation callback by forwarding to API endpoint"""
    with current_app.test_request_context('/payments/confirmation', method='POST'):
        csrf = CSRFProtect()
        csrf.init_app(current_app)
        csrf.disable()
    try:
        # Forward the request to the API endpoint
        api_url = f"{current_app.config['API_BASE_URL']}/api/v1/payments/confirmation"
        response = requests.post(api_url, json=request.get_json())
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error forwarding M-Pesa confirmation to API: {str(e)}")
        return jsonify({
            "ResultCode": "0",
            "ResultDesc": "Success"
        }), 200

@main.route('/payments/validation', methods=['POST'])
@require_safaricom_ip_validation
def mpesa_validation():
    print(request.json)
    """Handle M-Pesa validation requests by forwarding to API endpoint"""
    with current_app.test_request_context('/payments/confirmation', method='POST'):
        csrf = CSRFProtect()
        csrf.init_app(current_app)
        csrf.disable()
    try:
        # Forward the request to the API endpoint
        api_url = f"{current_app.config['API_BASE_URL']}/api/v1/payments/validation"
        response = requests.post(api_url, json=request.get_json())
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logger.error(f"Error forwarding M-Pesa validation to API: {str(e)}")
        return jsonify({
            "ResultCode": 1,
            "ResultDesc": "Internal server error"
        }), 200

@main.route('/search',methods=['GET', 'POST'])
def search():
    query = request.args.get('query')
    search_type = request.args.get('searchType') 
    # Check if search_type is provided
    # if not search_type:
    #     flash("Please select a category to search.", "warning")
    #     return redirect(url_for('main.search')) 

    results = {
        'members': [],
        'payments': [],
        'blocks': [],
        'zones': []
    }

    if query:
        # Search based on the selected search type
        if search_type == 'members':
            members = UserModel.query.filter(
                (UserModel.full_name.ilike(f"%{query}%")) |
                (UserModel.email.ilike(f"%{query}%")) |
                (UserModel.id_number.ilike(f"%{query}%")) |
                (UserModel.phone_number.ilike(f"%{query}%")) | 
                (UserModel.bank_id.ilike(f"%{query}%")) |
                (UserModel.acc_number.ilike(f"%{query}%"))
            ).all()
            results['members'] = members

        elif search_type == 'payments':
            payments = PaymentModel.query.filter(
                (PaymentModel.mpesa_id.ilike(f"%{query}%")) |
                (PaymentModel.account_number.ilike(f"%{query}%")) |
                (PaymentModel.source_phone_number.ilike(f"%{query}%")) |
                (PaymentModel.amount.ilike(f"%{query}%"))
            ).all()
            results['payments'] = payments

        elif search_type == 'blocks':
            blocks = BlockModel.query.filter(
                BlockModel.name.ilike(f"%{query}%")
            ).all()
            results['blocks'] = blocks

        elif search_type == 'zones':
            zones = ZoneModel.query.filter(
                ZoneModel.name.ilike(f"%{query}%")
            ).all()
            results['zones'] = zones

    return render_template('search_results.html', query=query, search_type=search_type, results=results)

@main.route('/block/<int:block_id>')
@login_required
@approval_required
def view_block(block_id):
    umbrella = get_umbrella_by_user(current_user.id)
    block = BlockModel.query.filter_by(id=block_id,parent_umbrella_id=umbrella['id']).first()

    # Pass block details to the home page
    return render_template('search_results.html', block=block)


@main.route('/blocks', methods=['GET'])
@login_required
@approval_required
def view_all_blocks():
    try:
        umbrella = get_umbrella_by_user(current_user.id)
        if not umbrella:
            flash('No umbrella association found.', 'warning')
            return render_template('all_blocks.html', blocks=[])
            
        blocks = get_blocks_by_umbrella()
        if not blocks:
            return render_template('all_blocks.html', blocks=[])
        
        block_data = []
        members = get_members()
        for block in blocks:
            block_members = [
                member for member in members 
                if any(block_membership['id'] == block['id'] for block_membership in member.get('block_memberships', []))
            ]     
            block_data.append({
                'name': block['name'],
                'parent_umbrella': umbrella['name'] if umbrella['name'] else 'N/A',
                'members': len(block_members)
            })

        return render_template('all_blocks.html', blocks=block_data)
    except Exception as e:
        current_app.logger.error(f"Error in view_all_blocks: {str(e)}")
        flash('Error retrieving blocks. Please try again later.', 'danger')
        return render_template('all_blocks.html', blocks=[])

#For Cascade dropdown - AJAX
@main.route('/get_zones/<int:block_id>')
@login_required
def get_zones(block_id):
    """Endpoint to get zones for a specific block"""
    try:
        zones = get_zones_by_block(block_id)
        
        if not zones:
            return jsonify({'zones': [], 'message': 'No zones found for this block'}), 200
            
        # Format zones for JSON response if needed
        zones_list = [{'id': zone['id'], 'name': zone['name']} for zone in zones]
        
        return jsonify(zones_list)
    except Exception as e:
        logging.error(f"Error fetching zones for block {block_id}: {str(e)}")
        return jsonify({'error': 'Error fetching zones. Please try again.'}), 500

@main.route('/get_members/<zone_id>')
@login_required
def get_members_for_zone(zone_id):
    try:
        umbrella = get_umbrella_by_user(current_user.id)
        members = get_members_by_zone(zone_id, umbrella.get('id')) if umbrella else []
        return jsonify([{"id": str(member["id"]), "name": member["full_name"]} for member in members])
    except Exception as e:
        return jsonify([]), 500

@main.route('/get_filtered_members/<int:block_id>', methods=['GET'])
@main.route('/get_filtered_members/<int:block_id>/<int:zone_id>', methods=['GET'])
def get_filtered_members(block_id, zone_id=None):
    if zone_id:
        # Filter by both block and zone
        members = UserModel.query.join(UserModel.block_memberships).join(UserModel.zone_memberships)\
            .filter(BlockModel.id == block_id, ZoneModel.id == zone_id).all()
    else:
        # Filter by block only
        members = UserModel.query.join(UserModel.block_memberships)\
            .filter(BlockModel.id == block_id).all()

    return jsonify([{
        'id': member.id,
        'full_name': member.full_name,
        'phone_number': member.phone_number,
        'id_number': member.id_number,
        'membership_info': ' '.join([
            f"{block.name} ({zone.name})"
            for block, zone in zip(member.block_memberships, member.zone_memberships)
        ]),
        'bank_name': member.bank.name if member.bank else '',
        'acc_number': member.acc_number or ''
    } for member in members])

@main.route('/get_contribution_stats/<int:block_id>', methods=['GET'])
@main.route('/get_contribution_stats/<int:block_id>/<int:zone_id>', methods=['GET'])
def get_contribution_stats(block_id, zone_id=None):
    try:
        # Base query to get users
        base_query = UserModel.query.join(UserModel.block_memberships)

        # Filter by block and optionally by zone
        if zone_id:
            base_query = base_query.join(UserModel.zone_memberships)\
                .filter(BlockModel.id == block_id, ZoneModel.id == zone_id)
        else:
            base_query = base_query.filter(BlockModel.id == block_id)

        # Get all users in the block/zone
        users = base_query.all()
        total_users = len(users)

        # Count users who have made payments
        contributed = 0
        for user in users:
            # Use PaymentModel to check if user has payments
            payment_exists = PaymentModel.query.filter_by(
                payer_id=user.id,
                block_id=block_id
            ).first() is not None
            if payment_exists:
                contributed += 1

        pending = total_users - contributed

        return jsonify({
            'contributed': contributed,
            'pending': pending
        })
    except Exception as e:
        print(f"Error getting contribution stats: {str(e)}")
        return jsonify({'error': 'Error getting contribution stats'}), 500

@main.route('/get_user_by_id/<id_number>')
@login_required
def get_user_by_id(id_number):
    try:
        user = get_user_by_id_number(id_number)
        print(f"Raw API Response for user {id_number}: {user}")  # Debug print
        
        if user and isinstance(user, dict):
            # Extract data directly from the response
            full_name = user.get('full_name', '')
            phone_number = user.get('phone_number', '')
            
            # Get block data from block_memberships
            block_memberships = user.get('block_memberships', [])
            block_id = str(block_memberships[0]['id']) if block_memberships else ''
            block_name = block_memberships[0]['name'] if block_memberships else ''
            
            print(f"Extracted data: full_name={full_name}, block_id={block_id}, block_name={block_name}, phone={phone_number}")
            
            response_data = {
                'success': True,
                'data': {
                    'full_name': full_name,
                    'block': block_name,
                    'block_id': block_id,
                    'phone_number': phone_number
                }
            }
            print(f"Sending response: {response_data}")
            return jsonify(response_data)
            
        print(f"No user found for ID: {id_number}")
        return jsonify({'success': False, 'message': 'User not found'})
    except Exception as e:
        print(f"Error in get_user_by_id: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@main.route('/get_member_contributions', methods=['GET'])
@login_required
def get_filtered_member_contributions():
    try:
        # Get filter parameters from request
        block_id = request.args.get('block_id')
        zone_id = request.args.get('zone_id')
        host_id = request.args.get('host_id')
        member_id = request.args.get('member_id')
        status = request.args.get('status')

        # Get umbrella ID for the current user
        umbrella = get_umbrella_by_user(current_user.id)
        if not umbrella:
            return jsonify({'error': 'No umbrella found'}), 404

        # Prepare base query parameters
        params = {'role': 'Member', 'umbrella_id': umbrella['id']}
        
        # Add block and zone filters if provided
        if block_id:
            params['block_id'] = block_id
        if zone_id:
            params['zone_id'] = zone_id

        # Fetch filtered members
        members_response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/users/",
            params=params
        )
        
        if members_response.status_code != 200:
            return jsonify({'error': 'Error fetching members'}), 500

        members = members_response.json()

        # Get current meeting details
        meeting = get_upcoming_meeting_details()
        if not meeting:
            return jsonify({'error': 'No upcoming meeting found'}), 404

        meeting_id = meeting['meeting_id']
        host_name = meeting['host']
        meeting_date = meeting['when']

        # Prepare contribution query parameters
        contributions_params = {'meeting_id': meeting_id}
        if host_id:
            # Verify that the host belongs to the umbrella's blocks
            host_response = requests.get(
                f"{current_app.config['API_BASE_URL']}/api/v1/users/{host_id}"
            )
            if host_response.status_code != 200:
                flash("Error fetching host details.", "danger")
                return []
            
            host_data = host_response.json()
            host_blocks = host_data.get('block_memberships', [])
            if not any(block['parent_umbrella_id'] == umbrella['id'] for block in host_blocks):
                flash("You do not have permission to view this host's contributions.", "danger")
                return []
            
            contributions_params['host_id'] = host_id

        if member_id and member_id != 'all_members':
            contributions_params['payer_id'] = member_id

        if status:
            contributions_params['status'] = status

        contributions_response = requests.get(
            f"{current_app.config['API_BASE_URL']}/api/v1/payments/",
            params=contributions_params
        )

        if contributions_response.status_code != 200:
            return jsonify({'error': 'Error fetching contributions'}), 500

        contributions = contributions_response.json()

        # Combine and filter member contributions
        member_contributions = []
        for member in members:
            contribution_record = next(
                (c for c in contributions if c['payer_id'] == member['id']), 
                None
            )

            member_status = ('Contributed' 
                           if contribution_record and contribution_record['transaction_status']
                           else 'Pending')

            # Apply status filter if provided
            if status and status != member_status:
                continue

            member_contributions.append({
                'full_name': member['full_name'],
                'amount': contribution_record['amount'] if contribution_record else 0.0,
                'status': member_status
            })

        return jsonify({
            'member_contributions': member_contributions,
            'host_name': host_name,
            'meeting_date': meeting_date
        })

    except Exception as e:
        print(f"Error in get_filtered_member_contributions: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

