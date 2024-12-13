from ..utils import db
from flask import current_app
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore
import uuid
from ..utils import db
from flask_security import UserMixin, RoleMixin
import uuid
from datetime import datetime, timezone
import string
import random
from sqlalchemy import event

# Association tables
member_blocks = db.Table('member_blocks',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('block_id', db.Integer, db.ForeignKey('blocks.id'), primary_key=True)
)
member_zones = db.Table(
    'member_zones',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('zone_id', db.Integer, db.ForeignKey('zones.id'), primary_key=True)
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
    id_number = db.Column(db.Integer, index=True)
    phone_number = db.Column(db.String(80))
    active = db.Column(db.Boolean, default=True)
    
    # Flask-Security tracking fields
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer, default=0)
    confirmed_at = db.Column(db.DateTime())
    
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'))
    acc_number = db.Column(db.String(50))
    image_file = db.Column(db.String(50), nullable=False, default='profile.png')
    registered_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'))
    umbrella_id = db.Column(db.Integer, db.ForeignKey('umbrellas.id'))
    __table_args__ = (db.UniqueConstraint('id_number', 'phone_number',acc_number, 'zone_id', name='uq_user_id_phone_acc_zone'),)


    is_approved = db.Column(db.Boolean(), default=False)  # New field
    approval_date = db.Column(db.DateTime())  # New field
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.relationship('UserModel', remote_side=[id],
                                backref='approved_users')
    
    def approve(self, approved_by):
        # current_app.logger.debug(f"Approving user {self.id}")
        self.is_approved = True
        self.roles.append(RoleModel.query.filter_by(name='Administrator').first())
        self.approval_date = datetime.now(timezone.utc)
        self.approved_by_id = approved_by.id
        # current_app.logger.debug(f"User {self.id} approved by {approved_by.id}")
        db.session.commit()
        # current_app.logger.debug(f"Approval for user {self.id} committed to database")

    def unapprove(self):
        self.is_approved = False
        self.approval_date = None
        self.roles.pop(RoleModel.query.filter_by(name='Administrator').first())
        self.approved_by_id = None
        db.session.commit()

     # composite unique constraint


    
    # Relationships
    roles = db.relationship('RoleModel', secondary=roles_users, backref=db.backref('users', lazy=True))
    messages = db.relationship('CommunicationModel', backref='author', lazy=True)
    payments = db.relationship('PaymentModel', backref='payer', lazy=True)
    block_memberships = db.relationship('BlockModel',secondary=member_blocks,backref=db.backref('block_members', lazy='dynamic'),lazy='dynamic')
    zone_memberships = db.relationship('ZoneModel', secondary=member_zones, backref=db.backref('zone_members', lazy=True))
    webauth = db.relationship('WebAuth', backref='user', uselist=False)
    hosted_meetings = db.relationship('MeetingModel', backref='host', foreign_keys='MeetingModel.host_id')

    def __repr__(self):
        return f"<User {self.full_name}>"
    
    # @staticmethod
    # def generate_member_identifier(umbrella, block):
    #     """
    #     Generate a unique identifier for a member based on the umbrella and block.
    #     Format: {UmbrellaInitials}{BlockInitials}{Increment}
    #     Example: NYB001
    #     """        
    #     # Ensure initials are present
    #     if not umbrella.initials:
    #         raise ValueError("Umbrella initials cannot be None.")
    #     if not block.initials:
    #         raise ValueError("Block initials cannot be None.")

    #     # Combine initials
    #     prefix = f"{umbrella.initials}{block.initials}"

    #     # Query existing unique_ids in member_blocks for this umbrella and block
    #     last_identifier = db.session.query(member_blocks.c.unique_id).join(BlockModel, member_blocks.c.block_id == BlockModel.id).filter(
    #         member_blocks.c.unique_id.like(f"{prefix}%"),
    #         BlockModel.parent_umbrella_id == umbrella.id
    #     ).order_by(member_blocks.c.unique_id.desc()).first()

    #     # Determine the next incremental number
    #     if last_identifier:
    #         try:
    #             last_number = int(last_identifier[0][-3:])
    #             new_number = f"{last_number + 1:03}"
    #         except ValueError:
    #             # Handle cases where the last three characters are not digits
    #             new_number = "001"
    #     else:
    #         new_number = "001"

    #     # Construct the unique_id
    #     unique_id = f"{prefix}{new_number}"
    #     return unique_id



class WebAuth(db.Model):
    __tablename__ = 'webauth'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    auth_token = db.Column(db.String(255), unique=True, nullable=False)

class UmbrellaModel(db.Model):
    __tablename__ = 'umbrellas'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    location = db.Column(db.String(255), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    blocks = db.relationship('BlockModel', backref='parent_umbrella', lazy=True)
    initials = db.Column(db.String(10), unique=True)

    def __repr__(self):
        return f"<Umbrella {self.name}>"
    
    @staticmethod
    def generate_unique_initials(name):
        # Start with the first two characters of the name
        initials = name[:2].upper()
        existing_initials = {umbrella.initials for umbrella in UmbrellaModel.query.all()}

        # Add letters until initials are unique
        suffix = 2
        while initials in existing_initials:
            initials = name[:suffix].upper()
            suffix += 1
        return initials
    

class BlockModel(db.Model):
    __tablename__ = 'blocks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_umbrella_id = db.Column(db.Integer, db.ForeignKey('umbrellas.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    zones = db.relationship('ZoneModel', backref='parent_block', lazy=True)
    payments = db.relationship('PaymentModel', backref='block', lazy=True)
    meetings = db.relationship('MeetingModel', backref='block', lazy=True)
    initials = db.Column(db.String(10))

        # Role-specific relationships (Chairman, Secretary, Treasurer)
    chairman_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    chairman = db.relationship('UserModel', foreign_keys=[chairman_id], backref='chaired_blocks')

    secretary_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    secretary = db.relationship('UserModel', foreign_keys=[secretary_id], backref='secretary_blocks')

    treasurer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    treasurer = db.relationship('UserModel', foreign_keys=[treasurer_id], backref='treasurer_blocks')


    def __repr__(self):
        return f"<Block {self.name}>"
    
    @staticmethod
    def block_initials(name):
        initials = f'{name[0].upper()}{name[-1].upper()}'
        return initials
    
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
    unique_id = db.Column(db.String(16), unique=True, nullable=False, index=True)
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    block_id = db.Column(db.Integer, db.ForeignKey('blocks.id'), nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'), nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.DateTime, nullable=False)
    payments = db.relationship('PaymentModel', backref='meeting', lazy=True)  


    def __repr__(self):
        return f"<Meeting {self.unique_id} on {self.date}>"

def generate_unique_meeting_id(length=5):
    """Generates a unique alphanumeric ID for a meeting."""
    characters = string.ascii_uppercase + string.digits
    while True:
        unique_id = ''.join(random.choices(characters, k=length))
        if not MeetingModel.query.filter_by(unique_id=unique_id).first():
            return unique_id

@event.listens_for(MeetingModel, 'before_insert')
def receive_before_insert(mapper, connection, target):
    """Assign a unique_id before inserting a new MeetingModel record."""
    if not target.unique_id:
        target.unique_id = generate_unique_meeting_id()

class BankModel(db.Model):
    __tablename__ = 'banks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False,unique=True)
    paybill_no = db.Column(db.String(80), nullable=False,unique=True)
    total_transactions = db.relationship('PaymentModel', backref='bank', lazy=True)
    users = db.relationship('UserModel', backref='bank', lazy=True)

    def __repr__(self):
        return f"<Bank {self.name}>"

class PaymentModel(db.Model):
    """Model for storing payments including M-Pesa transactions"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    mpesa_id = db.Column(db.String(255), nullable=False)  # TransID from M-Pesa
    account_number = db.Column(db.String(80), nullable=False)  # BillRefNumber
    source_phone_number = db.Column(db.String(80), nullable=False)  # MSISDN
    amount = db.Column(db.Integer, nullable=False)
    payment_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    transaction_status = db.Column(db.String, default='Pending')
    
    # Payment status tracking
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    status_reason = db.Column(db.String(255))  # Reason for failure if any
    checkout_request_id = db.Column(db.String(100))  # For STK push tracking
    merchant_request_id = db.Column(db.String(100))  # For STK push tracking
    
    # Timestamps for different stages
    initiated_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    validated_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    failed_at = db.Column(db.DateTime)
    
    # Number of retry attempts for failed payments
    retry_count = db.Column(db.Integer, default=0)
    last_retry_at = db.Column(db.DateTime)
    
    # Bank and block relationships
    umbrella_id = db.Column(db.Integer, db.ForeignKey('umbrellas.id'), nullable=True)
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=True)
    block_id = db.Column(db.Integer, db.ForeignKey('blocks.id'), nullable=True)
    payer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=True)
    
    # Additional M-Pesa fields
    transaction_type = db.Column(db.String(50))  # e.g., CustomerPayBillOnline
    business_short_code = db.Column(db.String(20))
    invoice_number = db.Column(db.String(50))
    org_account_balance = db.Column(db.Float)
    third_party_trans_id = db.Column(db.String(50))
    first_name = db.Column(db.String(50))
    middle_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<Payment {self.mpesa_id}>'

    @property
    def customer_name(self):
        """Get full customer name"""
        names = filter(None, [self.first_name, self.middle_name, self.last_name])
        return ' '.join(names)

    def to_dict(self):
        """Convert payment to dictionary"""
        return {
            'id': self.id,
            'mpesa_id': self.mpesa_id,
            'transaction_type': self.transaction_type,
            'account_number': self.account_number,
            'source_phone_number': self.source_phone_number,
            'amount': self.amount,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'transaction_status': self.transaction_status,
            'bank_id': self.bank_id,
            'block_id': self.block_id,
            'payer_id': self.payer_id,
            'meeting_id': self.meeting_id,
            'business_short_code': self.business_short_code,
            'invoice_number': self.invoice_number,
            'org_account_balance': self.org_account_balance,
            'third_party_trans_id': self.third_party_trans_id,
            'customer_name': self.customer_name
        }

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