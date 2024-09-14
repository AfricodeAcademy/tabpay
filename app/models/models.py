from app.extensions import db

# Association table for many-to-many relationship between User and Communications (messages)
# user_message_association = db.Table('user_message_association',
#     db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
#     db.Column('message_id', db.Integer, db.ForeignKey('communications.id'), primary_key=True)
# )

# Association table for many-to-many relationship between User and Payments
# user_payment_association = db.Table('user_payment_association',
#     db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
#     db.Column('payment_id', db.Integer, db.ForeignKey('payments.id'), primary_key=True)
# )

# Association table for many-to-many relationship between User and Block
# user_block_association = db.Table('user_block_association',
#     db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
#     db.Column('block_id', db.Integer, db.ForeignKey('blocks.id'), primary_key=True)
# )

class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(255), nullable=False)
    lname = db.Column(db.String(255), nullable=False)
    # username = db.Column(db.String(80), unique=True, nullable=False)  
    # email = db.Column(db.String(255), unique=True, nullable=False)
    # password = db.Column(db.String(80), nullable=False)
    # id_number = db.Column(db.Integer, nullable=False)
    # age = db.Column(db.Integer, nullable=True)
    # phone = db.Column(db.Integer, unique=True, nullable=False)
    # location = db.Column(db.String(255), nullable=True)
    # gender = db.Column(db.String(255), nullable=True)
    # user_type = db.Column(db.String(255), nullable=False)
    # block_membership = db.Column(db.String(255), nullable=False)
    # registered_at = db.Column(db.DateTime, server_default=db.func.now())
    # updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    # is_active_member = db.Column(db.Boolean, nullable=False, default=True)
    
    # One-to-many relationships
    # messages = db.relationship('CommunicationModel', backref='author', lazy=True)
    # payments = db.relationship('PaymentModel', backref='payee', lazy=True)
    # blocks_led = db.relationship('BlockModel', backref='block_leader', lazy=True)
    
    # Many-to-many relationships
    # message_recipients = db.relationship('CommunicationModel', secondary=user_message_association, backref='recipients', lazy='dynamic')
    # payment_participants = db.relationship('PaymentModel', secondary=user_payment_association, backref='participants', lazy='dynamic')
    # block_memberships = db.relationship('BlockModel', secondary=user_block_association, backref='members', lazy='dynamic')


class CommunicationModel(db.Model):
    __tablename__ = 'communications'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    # user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # created_at = db.Column(db.DateTime, server_default=db.func.now())
    # updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Many-to-many relationship with User is already handled in UserModel


class PaymentModel(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    # payee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    # payment_date = db.Column(db.Date, nullable=False)
    # bank = db.Column(db.String, nullable=True)
    # acc_number = db.Column(db.Integer, nullable=False)
    # payment_method = db.Column(db.String, nullable=True)
    # created_at = db.Column(db.DateTime, server_default=db.func.now())
    # updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    # status = db.Column(db.Boolean, default=True)

    # Many-to-many relationship with User is already handled in UserModel


class BlockModel(db.Model):
    __tablename__ = 'blocks'

    id = db.Column(db.Integer, primary_key=True)
    block_name = db.Column(db.String(255), nullable=False)
    # member_count = db.Column(db.Integer, nullable=False)
    # block_leader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # block_transactions = db.Column(db.Float, nullable=False)
    # umbrella_id = db.Column(db.Integer, db.ForeignKey('umbrellas.id'), nullable=False)
    # created_at = db.Column(db.DateTime, server_default=db.func.now())
    # updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Many-to-many relationship with User is already handled in UserModel

    # Relationship with zones
    # zones = db.relationship('ZoneModel', backref='parent_block', lazy=True)


class UmbrellaModel(db.Model):
    __tablename__ = 'umbrellas'
    
    id = db.Column(db.Integer, primary_key=True)
    umbrella_name = db.Column(db.String(255), nullable=False)
    # location = db.Column(db.String(255), nullable=False)
    # umbrella_blocks = db.relationship('BlockModel', backref='parent_umbrella', lazy=True)


class ZoneModel(db.Model):
    __tablename__ = 'zones'
    
    id = db.Column(db.Integer, primary_key=True)
    zone_name = db.Column(db.String(255), nullable=False)
    # parent_block_id = db.Column(db.Integer, db.ForeignKey("blocks.id"), nullable=False)
