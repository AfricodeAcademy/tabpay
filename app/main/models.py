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
    db.Column('block_id', db.Integer, db.ForeignKey('blocks.id'), primary_key=True),
    db.Column('unique_id', db.String(20), unique=True) 
)

member_zones = db.Table(
    'member_zones',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('zone_id', db.Integer, db.ForeignKey('zones.id'), primary_key=True),
    db.Column('umbrella_id', db.Integer, db.ForeignKey('umbrellas.id'), nullable=False),  
    db.UniqueConstraint('user_id', 'zone_id',  name='uq_user_zone')  
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
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'))
    acc_number = db.Column(db.String(50))
    image_file = db.Column(db.String(20), nullable=False, default='profile.png')
    registered_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'))
    confirmed_at = db.Column(db.DateTime)
    umbrella_id = db.Column(db.Integer, db.ForeignKey('umbrellas.id'))
 
    is_approved = db.Column(db.Boolean(), default=False)  # New field
    approval_date = db.Column(db.DateTime())  # New field
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by = db.relationship('UserModel', remote_side=[id],
                                backref='approved_users')
    
    def approve(self, approved_by):
        current_app.logger.debug(f"Approving user {self.id}")
        self.is_approved = True
        self.roles.append(RoleModel.query.filter_by(name='Administrator').first())
        self.approval_date = datetime.now(timezone.utc)
        self.approved_by_id = approved_by.id
        current_app.logger.debug(f"User {self.id} approved by {approved_by.id}")
        db.session.commit()
        current_app.logger.debug(f"Approval for user {self.id} committed to database")

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
    
    @staticmethod
    def generate_member_identifier(umbrella, block):
        """
        Generate a unique identifier for a member based on the umbrella and block.
        Format: {UmbrellaInitials}{BlockInitials}{Increment}
        Example: NYB001
        """        
        # Ensure initials are present
        if not umbrella.initials:
            raise ValueError("Umbrella initials cannot be None.")
        if not block.initials:
            raise ValueError("Block initials cannot be None.")

        # Combine initials
        prefix = f"{umbrella.initials}{block.initials}"

        # Query existing unique_ids in member_blocks for this umbrella and block
        last_identifier = db.session.query(member_blocks.c.unique_id).join(BlockModel, member_blocks.c.block_id == BlockModel.id).filter(
            member_blocks.c.unique_id.like(f"{prefix}%"),
            BlockModel.parent_umbrella_id == umbrella.id
        ).order_by(member_blocks.c.unique_id.desc()).first()

        # Determine the next incremental number
        if last_identifier:
            try:
                last_number = int(last_identifier[0][-3:])
                new_number = f"{last_number + 1:03}"
            except ValueError:
                # Handle cases where the last three characters are not digits
                new_number = "001"
        else:
            new_number = "001"

        # Construct the unique_id
        unique_id = f"{prefix}{new_number}"
        return unique_id



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

def generate_unique_meeting_id(length=10):
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