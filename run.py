from app import create_app
from app.extensions import db
from app.models.models import user_datastore
from flask_security.utils import hash_password
from flask import render_template,request
from app.models.models import BlockModel,UserModel,PaymentModel







app = create_app()


@app.route('/', methods=['GET'])
def home():
    return render_template('index.html', title='TabPay | Home')



@app.route('/statistics', methods=['GET'])
def statistics():
    return render_template('statistics.html', title='Dashboard | Statistics')



@app.route('/manage_contribution', methods=['GET'])
def manage_contribution():
    return render_template('manage_contribution.html', title='Dashboard | Manage Contributions')


@app.route('/host', methods=['GET'])
def host():
    return render_template('host.html', title='Dashboard | Host')


@app.route('/settings', methods=['GET'])
def settings():
    return render_template('settings.html', title='Dashboard | Settings')



@app.route('/block_reports', methods=['GET', 'POST'])
def block_reports():
    block_filter = request.args.get('block')
    member_filter = request.args.get('member')
    date_filter = request.args.get('date')
    
  
    blocks = BlockModel.query.all()
    members = UserModel.query.all()

    
    contributions_query = PaymentModel.query

   
    if block_filter:
        block = BlockModel.query.filter_by(name=block_filter).first()
        if block:
            members_in_block = [member.id for member in block.members]
            contributions_query = contributions_query.filter(Contribution.member_id.in_(members_in_block))

   
    if member_filter:
        member = Member.query.filter_by(name=member_filter).first()
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




@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))




with app.app_context():
    db.create_all()

    #Create roles
    user_datastore.find_or_create_role(name='admin',description='system developer')
    user_datastore.find_or_create_role(name='owner',description='owner of the system')

    #Create admin user
    if not user_datastore.find_user(email='testadmin@gmail.com'):
        hashed_password = hash_password('password')
        user_datastore.create_user(email='testadmin@gmail.com',password=hashed_password,full_name='Test Admin',id_number='123456',roles=[user_datastore.find_role('admin')])
        db.session.commit()
        print('Admin user created successfully.')

if __name__ == "__main__":
    app.run(debug=True,port=5001)
