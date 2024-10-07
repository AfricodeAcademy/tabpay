from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_security import login_required, roles_required, current_user, logout_user, roles_accepted
from flask_security.utils import hash_password
from ..utils import db
from ..main.forms import ProfileForm, AddMemberForm, AddCommitteForm, UmbrellaForm, BlockForm, ZoneForm, ScheduleForm
from .models import UserModel, Role, BlockModel, ZoneModel, UmbrellaModel, BankModel, MeetingModel, PaymentModel
from app import user_datastore
from app.api.api import BlockReportsResource, BlocksResource, UmbrellasResource, ZonesResource, UsersResource
from flask_wtf.csrf import generate_csrf


main = Blueprint('main', __name__)
@main.route('/', methods=['GET'])
def home():
    return render_template('index.html', title='TabPay | Home')

@main.route('/settings', methods=['GET', 'POST'])
@login_required
@roles_accepted('Admin', 'SuperUser', 'Chairman', 'Secretary')
def settings():
    active_tab = request.args.get('active_tab', 'profile')
    
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'profile':
            return handle_profile_update()
        elif form_type == 'umbrella':
            return handle_umbrella_creation()
        elif form_type == 'committee':
            return handle_committee_addition()
        elif form_type == 'block':
            return handle_block_creation()
        elif form_type == 'zone':
            return handle_zone_creation()
        elif form_type == 'member':
            return handle_member_creation()
    
    return render_settings_page(active_tab)



@main.route('/statistics', methods=['GET'])
@login_required
@roles_accepted('SuperUser', 'Admin')
def statistics():
    included_roles = ['Member', 'Chairman', 'Secretary', 'SuperUser']
    total_members = UserModel.query.join(UserModel.roles).filter(Role.name.in_(included_roles)).count()
    total_blocks = BlockModel.query.count()
    return render_template('statistics.html', title='Dashboard | Statistics', 
                           total_members=total_members, total_blocks=total_blocks, user=current_user)

@main.route('/manage_contribution', methods=['GET'])
@login_required
def manage_contribution():
    return render_template('manage_contribution.html', title='Dashboard | Manage Contributions')

@main.route('/host', methods=['GET', 'POST'])
@login_required
def host():
    schedule_form = ScheduleForm()
    if request.method == 'POST' and schedule_form.validate_on_submit():
        return schedule_meeting(schedule_form)
    
    blocks = BlockModel.query.filter_by(created_by=current_user.id).all()
    zones = ZoneModel.query.filter_by(created_by=current_user.id).all()
    members = UserModel.query.filter_by(zone=schedule_form.zone.data).all()
    
    return render_template('host.html', title='Dashboard | Host', user=current_user,
                           schedule_form=schedule_form, zones=zones, members=members, blocks=blocks)

@main.route('/block_reports', methods=['GET'])
@login_required
def block_reports():
    # Use the API endpoint to get block reports data
    block_reports_resource = BlockReportsResource()
    response = block_reports_resource.get()
    
    blocks = BlockModel.query.all()
    members = UserModel.query.all()
    
    return render_template('block_reports.html', 
                           blocks=blocks, 
                           members=members, 
                           contributions=response.get('detailed_contributions', []),
                           total_contributed=response.get('total_contributed', 0))



# Helper functions (these now use the API endpoints where appropriate)
def handle_profile_update():
    profile_form = ProfileForm()
    if profile_form.validate_on_submit():
        users_resource = UsersResource()
        response, status = users_resource.patch(current_user.id)
        if status == 200:
            flash('Profile updated successfully!', 'success')
        else:
            flash(response.get('message', 'Failed to update profile.'), 'danger')
    else:
        for field, errors in profile_form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    return redirect(url_for('main.settings', active_tab='profile'))

def handle_umbrella_creation():
    umbrella_form = UmbrellaForm()
    if umbrella_form.validate_on_submit():
        umbrellas_resource = UmbrellasResource()
        response, status = umbrellas_resource.post()
        if status == 201:
            flash('Umbrella created successfully!', 'success')
        else:
            flash(response.get('message', 'Failed to create umbrella.'), 'danger')
    else:
        for field, errors in umbrella_form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    return redirect(url_for('main.settings', active_tab='umbrella'))
#TODO to make this helper use the API endpoint
def handle_committee_addition():
    committee_form = AddCommitteForm()
    if committee_form.validate_on_submit():
        user = UserModel.query.filter_by(id_number=committee_form.id_number.data).first()
        if user:
            role_name = committee_form.role.data
            role = user_datastore.find_or_create_role(role_name)
            user_datastore.add_role_to_user(user, role)
            db.session.commit()
            flash(f'{user.full_name} added as {role_name}', 'success')
        else:
            flash('No member found with that ID!', 'danger')
    else:
        for field, errors in committee_form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    return redirect(url_for('main.settings', active_tab='committee'))

def handle_block_creation():
    block_form = BlockForm()
    if block_form.validate_on_submit():
        blocks_resource = BlocksResource()
        response, status = blocks_resource.post()
        if status == 201:
            flash('Block created successfully!', 'success')
        else:
            flash(response.get('message', 'Failed to create block.'), 'danger')
    else:
        for field, errors in block_form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    return redirect(url_for('main.settings', active_tab='block'))

def handle_zone_creation():
    zone_form = ZoneForm()
    if zone_form.validate_on_submit():
        zones_resource = ZonesResource()
        response, status = zones_resource.post()
        if status == 201:
            flash('Zone created successfully!', 'success')
        else:
            flash(response.get('message', 'Failed to create zone.'), 'danger')
    else:
        for field, errors in zone_form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    return redirect(url_for('main.settings', active_tab='zone'))

def handle_member_creation():
    member_form = AddMemberForm()
    if member_form.validate_on_submit():
        users_resource = UsersResource()
        response, status = users_resource.post()
        if status == 201:
            flash('Member created successfully!', 'success')
        else:
            flash(response.get('message', 'Failed to create member.'), 'danger')
    else:
        for field, errors in member_form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    return redirect(url_for('main.settings', active_tab='member'))

def render_settings_page(active_tab):
    profile_form = ProfileForm()
    umbrella_form = UmbrellaForm()
    committee_form = AddCommitteForm()
    block_form = BlockForm()
    zone_form = ZoneForm()
    member_form = AddMemberForm()
    
    user = UserModel.query.get(current_user.id)
    if user:
        profile_form.full_name.data = user.full_name
        profile_form.id_number.data = user.id_number

    umbrella = UmbrellaModel.query.filter_by(created_by=current_user.id).first()
    if umbrella:
        block_form.parent_umbrella.data = umbrella.name

    blocks = BlockModel.query.filter_by(created_by=current_user.id).all()
    zone_form.parent_block.choices = [(str(block.id), block.name) for block in blocks]

    zones = ZoneModel.query.filter_by(created_by=current_user.id).all()
    member_form.member_zone.choices = [(str(zone.id), zone.name) for zone in zones]

    banks = BankModel.query.all()
    member_form.bank.choices = [(str(bank.id), bank.name) for bank in banks]

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
                           csrf_token=generate_csrf())

def schedule_meeting(form):
    new_meeting = MeetingModel(
        block_id=form.block.data,
        zone_id=form.zone.data,
        members=form.members.data,
        date=form.date.data,
    )
    db.session.add(new_meeting)
    db.session.commit()
    flash('Meeting scheduled successfully!', 'success')
    return redirect(url_for('main.host'))

blueprint = main