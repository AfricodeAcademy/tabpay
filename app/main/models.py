from ..utils import db
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore
import uuid
from ..utils import db
from flask_security import UserMixin, RoleMixin
import uuid

# Association tables
member_blocks = db.Table('member_blocks',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('block_id', db.Integer, db.ForeignKey('blocks.id'), primary_key=True)
)

roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('block_id', db.Integer, db.ForeignKey('blocks.id'))  
)

class RoleModel(db.Model, RoleMixin):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        return f"<Role {self.name}>"

class UserModel(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    full_name = db.Column(db.String(255))
    id_number = db.Column(db.Integer, index=True, unique=True)
    phone_number = db.Column(db.String(80), unique=True)
    active = db.Column(db.Boolean, default=True)
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'))
    acc_number = db.Column(db.String(50))
    image_file = db.Column(db.String(20), nullable=False, default='profile.png')
    registered_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'))
    confirmed_at = db.Column(db.DateTime)

    # Relationships
    roles = db.relationship('RoleModel', secondary=roles_users, backref=db.backref('users', lazy=True))
    messages = db.relationship('CommunicationModel', backref='author', lazy=True)
    payments = db.relationship('PaymentModel', backref='payer', lazy=True)
    block_memberships = db.relationship('BlockModel', secondary=member_blocks, backref=db.backref('members', lazy=True))
    webauth = db.relationship('WebAuth', backref='user', uselist=False)
    hosted_meetings = db.relationship('MeetingModel', backref='host', foreign_keys='MeetingModel.host_id')

    def __repr__(self):
        return f"<User {self.full_name}>"

class WebAuth(db.Model):
    __tablename__ = 'webauth'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    auth_token = db.Column(db.String(255), unique=True, nullable=False)

class UmbrellaModel(db.Model):
    __tablename__ = 'umbrellas'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    location = db.Column(db.String(255), nullable=False, unique = True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blocks = db.relationship('BlockModel', backref='parent_umbrella', lazy=True)

    def __repr__(self):
        return f"<Umbrella {self.name}>"

class BlockModel(db.Model):
    __tablename__ = 'blocks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_umbrella_id = db.Column(db.Integer, db.ForeignKey('umbrellas.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    zones = db.relationship('ZoneModel', backref='parent_block', lazy=True)
    payments = db.relationship('PaymentModel', backref='block', lazy=True)
    meetings = db.relationship('MeetingModel', backref='block', lazy=True)

        # Role-specific relationships (Chairman, Secretary, Treasurer)
    chairman_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    chairman = db.relationship('UserModel', foreign_keys=[chairman_id], backref='chaired_blocks')

    secretary_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    secretary = db.relationship('UserModel', foreign_keys=[secretary_id], backref='secretary_blocks')

    treasurer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    treasurer = db.relationship('UserModel', foreign_keys=[treasurer_id], backref='treasurer_blocks')


    def __repr__(self):
        return f"<Block {self.name}>"
    
class ZoneModel(db.Model):
    __tablename__ = 'zones'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    parent_block_id = db.Column(db.Integer, db.ForeignKey('blocks.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # User who created the zone
    creator = db.relationship('UserModel', primaryjoin="ZoneModel.created_by == UserModel.id", backref='created_zones')  # Access the creator
    meetings = db.relationship('MeetingModel', backref='zone', lazy=True)  # Meetings in the zone

    # Members of the zone (users)
    members = db.relationship('UserModel', foreign_keys='UserModel.zone_id', backref='zone', lazy=True)

    def __repr__(self):
        return f"<Zone {self.name}>"


class MeetingModel(db.Model):
    __tablename__ = 'meetings'
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    block_id = db.Column(db.Integer, db.ForeignKey('blocks.id'), nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.DateTime, nullable=False)
    payments = db.relationship('PaymentModel', backref='meeting', lazy=True)  


    def __repr__(self):
        return f"<Meeting {self.id} on {self.date}>"

class BankModel(db.Model):
    __tablename__ = 'banks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    paybill_no = db.Column(db.Integer, nullable=False)
    total_transactions = db.relationship('PaymentModel', backref='bank', lazy=True)
    users = db.relationship('UserModel', backref='bank', lazy=True)

    def __repr__(self):
        return f"<Bank {self.name}>"

class PaymentModel(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    mpesa_id = db.Column(db.String(255), nullable=False)
    account_number = db.Column(db.String(80), nullable=False)
    source_phone_number = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    payment_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    transaction_status = db.Column(db.Boolean, default=False)
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=False)
    block_id = db.Column(db.Integer, db.ForeignKey('blocks.id'), nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=True) 


    def __repr__(self):
        return f"<Payment {self.amount} by {self.payer_id}>"

class CommunicationModel(db.Model):
    __tablename__ = 'communications'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    member_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"<Message from {self.member_id}>"

    
# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, UserModel, RoleModel)