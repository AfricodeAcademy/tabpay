from flask import Flask, request, jsonify, render_template
from flask_security import roles_accepted,login_required
from models import db, Block, Zone, Member, BlockMeeting
from flask_migrate import Migrate
from flask_cors import CORS
import uuid
from models import PaymentModel
# from run import owner,admin
# from ..extensions import main_blueprint




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)
CORS(app)

@app.route('/schedule_meeting', methods=['POST'])
def schedule_meeting():
    block_id = request.form.get('blockNumber')
    zone_id = request.form.get('zone')
    member_id = request.form.get('member')
    meeting_date = request.form.get('date')

    
    meeting = BlockMeeting(
        block_id=block_id,
        zone_id=zone_id,
        member_id=member_id,
        meeting_date=meeting_date
    )
    db.session.add(meeting)
    db.session.commit()

    return jsonify({'message': 'Meeting scheduled successfully'}), 201

# Route to render the form
@app.route('/')
def host():
    blocks = Block.query.all()
    return render_template('host.html', blocks=blocks)


@app.route('/upcoming_block/<int:block_id>', methods=['GET'])
def upcoming_block(block_id):
    block = Block.query.get_or_404(block_id)
    return render_template('upcoming_block.html', block=block)

# Route to generate payment link
@app.route('/upcoming_block/<int:block_id>', methods=['GET', 'POST'])
def upcoming_block(block_id):
    block = Block.query.get_or_404(block_id)
    payment_link = None

    if request.method == 'POST':
        # Create a payment entry
        new_payment = PaymentModel(
            mpesa_id=str(uuid.uuid4()),  # Example unique Mpesa ID
            account_number="Account123",   # Replace with actual logic to get account number
            source_phone_number="0700000000",  # Replace with actual logic to get the source phone number
            amount=1000,  # Replace with the actual amount
            block_id=block.id,
            payer_id=1  # Replace with actual user ID
        )
        db.session.add(new_payment)
        db.session.commit()

        # Generate a payment link (you can customize this as needed)
        payment_link = f"https://paymentgateway.com/pay/{new_payment.mpesa_id}"

    return render_template('upcoming_block.html', block=block, payment_link=payment_link)