from app import create_app
from app.extensions import db
from app.models.models import user_datastore
from flask_security.utils import hash_password
from app import create_app as app
from flask_security import  roles_required, current_user , login_required
from flask_security.utils import hash_password
from app.extensions import db
from app.models.models import UserModel,UmbrellaModel, BlockModel,ZoneModel,user_datastore
from app.forms.main import AddMemberForm,ProfileForm,AddCommitteForm,UmbrellaForm,BlockForm,ZoneForm
from flask import render_template, flash, redirect, url_for, jsonify, request


app = create_app()

from flask import render_template,redirect,url_for




@app.route('/settings', methods=['GET'])
@roles_required('Umbrella_creator')
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
@app.route('/settings/update_profile', methods=['POST'])
def update_profile():
    profile_form = ProfileForm()
    if profile_form.validate_on_submit():
        user = UserModel.query.filter_by(id=current_user.id).first()
        if user:
            user.full_name = profile_form.full_name.data
            user.id_number = profile_form.id_number.data
            if profile_form.password.data:
                user.password = hash_password(profile_form.password.data) 
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        else:
            flash('User not found!', 'danger')
        return redirect(url_for('settings'))
    else:
        flash('Form validation failed', 'danger')
        return redirect(url_for('settings'))


# Committee Addition Route
@app.route('/settings/add_committee', methods=['POST'])
def add_committee():
    committee_form = AddCommitteForm()

    if committee_form.validate_on_submit():
            
        full_name=committee_form.full_name.data,
        id_number=committee_form.id_number.data,
        phone_number=committee_form.phone_number.data,
        roles=committee_form.role.data
        
        role = user_datastore.find_or_create_role(roles)
        
        
        existing_committee_member = UserModel.query.filter_by(id_number=committee_form.id_number.data).first()
        if existing_committee_member:
            print('Committee member found')
            flash('Committee member with that id exists!', 'danger')
        
        new_committee_member =user_datastore.create_user(full_name=full_name,id_number=id_number,phone_number=phone_number)
        user_datastore.add_role_to_user(new_committee_member, role)
        db.session.commit()
        flash('Committee member added successfully', 'success')
    else:
        flash('Form validation failed, please check your input', 'danger')
        return redirect(url_for('settings'))  

              
#Umbrella Creation Route
@app.route('/settings/create_umbrella', methods=['POST'])
def create_umbrella():
    umbrella_form = UmbrellaForm()
    if umbrella_form.validate_on_submit():
        umbrella = UmbrellaModel.query.filter_by(name=umbrella_form.umbrella_name.data).first()
        if umbrella:
            flash('An umbrella with that name already exists', 'danger')
            

        else:
            new_umbrella = UmbrellaModel(
                name=umbrella_form.umbrella_name.data,
                location=umbrella_form.location.data,
                created_by=current_user.id
            )
            db.session.add(new_umbrella)
            db.session.commit()
            flash('Umbrella created successfully!', 'success')
        return redirect(url_for('settings'))
    else:
        flash('Form validation failed', 'danger')
        return redirect(url_for('settings'))


#Block Creation Route
@app.route('/settings/create_block', methods=['POST'])
def create_block():
    block_form = BlockForm()
    if block_form.validate_on_submit():
        block = BlockModel.query.filter_by(name=block_form.block_name.data).first()
        if block:
            flash('A block with that name already exists', 'danger')
        else:
            new_block = BlockModel(
                name=block_form.block_name.data,
                parent_umbrella_id=block_form.parent_umbrella.data,
                created_by=current_user.id
            )
            db.session.add(new_block)
            db.session.commit()
            flash('Block created successfully!', 'success')
        return redirect(url_for('settings'))
    else:
        flash('Form validation failed', 'danger')
        return redirect(url_for('settings'))


#Zone Creation Route
@app.route('/settings/create_zone', methods=['POST'])
def create_zone():
    zone_form = ZoneForm()
    if zone_form.validate_on_submit():
        zone = ZoneModel.query.filter_by(name=zone_form.zone_name.data).first()
        if zone:
            flash('A zone with that name already exists', 'danger')
        else:
            new_zone = ZoneModel(
                name=zone_form.zone_name.data,
                parent_block_id=zone_form.parent_block.data,
                created_by=current_user.id
            )
            db.session.add(new_zone)
            db.session.commit()
            flash('Zone created successfully!', 'success')
        return redirect(url_for('settings'))
    else:
        flash('Form validation failed', 'danger')
        return redirect(url_for('settings'))

#Member Creation Route
@app.route('/settings/add_member', methods=['POST'])
def add_member():
    member_form = AddMemberForm()
    if member_form.validate_on_submit():
        user = UserModel.query.filter_by(id_number=member_form.id_number.data).first()
        if user:
            flash('User with that ID already exists', 'danger')
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
            flash('Member added successfully', 'success')
        return redirect(url_for('settings'))
    else:
        flash('Form validation failed', 'danger')
        return redirect(url_for('settings'))




@app.route('/', methods=['GET'])
def home():
    return render_template('index.html', title='TabPay | Home')

@app.route('/statistics', methods=['GET'])
@login_required
@roles_required('Umbrella_creator')
def statistics():
    # Get total number of members
    total_members = UserModel.query.count()

    # Get total number of blocks
    total_blocks = BlockModel.query.count()

    return render_template('statistics.html', title='Dashboard | Statistics',  total_members=total_members,
        total_blocks=total_blocks, user=current_user
    )


@app.route('/manage_contribution', methods=['GET'])
def manage_contribution():
    
    return render_template('manage_contribution.html', title='Dashboard | Manage Contributions')


@app.route('/host', methods=['GET'])
def host():
    return render_template('host.html', title='Dashboard | Host')

@app.route('/block_reports', methods=['GET', 'POST'])
def block_reports():
    return render_template('block_reports.html', title='Dashboard | Block Reports')


@app.route('/logout')
def logout():
    return redirect(url_for('home'))


with app.app_context():
    db.create_all()

    #Create roles
    user_datastore.find_or_create_role(name='Umbrella_creator',description='Account owner')
    user_datastore.find_or_create_role(name='Chairman',description='Head of block')
    user_datastore.find_or_create_role(name='Secretary',description='block secretary')
    user_datastore.find_or_create_role(name='Member',description='Regular member')
   

    #Create Admin
    if not user_datastore.find_user(email='enockbett427@gmail.com'):
        hashed_password = hash_password('123456')
        user_datastore.create_user(email='enockbett427@gmail.com',password=hashed_password,roles=[user_datastore.find_role('Umbrella_creator')])
        db.session.commit()
        print('Umbrella_creator created successfully')

    #Create Chairman
    if not user_datastore.find_user(email='captain@example.com'):
        hashed_password = hash_password('123456')
        user_datastore.create_user(email='captain@example.com',password=hashed_password,roles=[user_datastore.find_role('Chairman')])
        db.session.commit()

    #Create Secretary
    if not user_datastore.find_user(email='secretary@example.com'):
        hashed_password = hash_password('123456')
        user_datastore.create_user(email='secretary@example.com',password=hashed_password,roles=[user_datastore.find_role('Secretary')])
        db.session.commit()

    #Create Members
    if not user_datastore.find_user(email='member1@example.com'):
        hashed_password = hash_password('123456')
        user_datastore.create_user(email='member1@example.com',password=hashed_password,roles=[user_datastore.find_role('Member')])
        db.session.commit()


if __name__ == "__main__":
    app.run(debug=True,port=5001)
