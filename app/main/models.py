from ..utils import db
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore
from flask_security.utils import hash_password
import uuid

# Association table for many-to-many relationship between User and Block
member_blocks = db.Table('member_blocks',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('block_id', db.Integer, db.ForeignKey('blocks.id'), primary_key=True)
)

# Association table for many-to-many relationship between User and Role
roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    
  
    def __repr__(self):
        return f"<Role {self.name}>"

class UserModel(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True) 
    password = db.Column(db.String(255)) 
    full_name = db.Column(db.String(255))
    id_number = db.Column(db.Integer, index=True,unique=True)  
    phone_number = db.Column(db.String(80), unique=True)
    active = db.Column(db.Boolean, default=True)
    bank = db.Column(db.Integer, db.ForeignKey('banks.id'))
    acc_number = db.Column(db.String(50))
    image_file = db.Column(db.String(20), nullable=False, default = 'profile.png')
    registered_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'))
    confirmed_at = db.Column(db.DateTime)
    webauth = db.relationship('WebAuth', backref='user', uselist=False)


    # Relationships
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    messages = db.relationship('CommunicationModel', backref='author', lazy=True)
    payments = db.relationship('PaymentModel', backref='payer', lazy=True)
    organized_meetings = db.relationship('MeetingModel', backref='meeting_organizer', lazy=True)

    # Many-to-many relationship with blocks
    block_memberships = db.relationship('BlockModel', secondary=member_blocks, backref=db.backref('users', lazy=True))

    # Password auto-generation method
    def generate_auto_password(self):
        import random, string
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        self.password = hash_password(password) 
        return password  
    
    def __repr__(self):
        return f"<Member {self.full_name}>"

class WebAuth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    auth_token = db.Column(db.String(255), unique=True, nullable=False)

class UmbrellaModel(db.Model):
    __tablename__ = 'umbrellas'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    location = db.Column(db.String(255), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'),nullable=False)  
    blocks = db.relationship('BlockModel', backref='parent_umbrella', lazy=True)

    def __repr__(self):
        return f"<Umbrella {self.name}>"
    
class BlockModel(db.Model):
    __tablename__ = 'blocks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_umbrella_id = db.Column(db.Integer, db.ForeignKey('umbrellas.id'), nullable=False)
    zones = db.relationship('ZoneModel', backref='parent_block', lazy=True)
    payments = db.relationship('PaymentModel', backref='block_payments', lazy=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    meetings = db.relationship('MeetingModel', backref='hosting_block', lazy=True)



    def __repr__(self):
        return f"<Zone {self.name}>"
     

   
class ZoneModel(db.Model):
    __tablename__ = 'zones'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    parent_block_id = db.Column(db.Integer, db.ForeignKey("blocks.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
                           
    meetings = db.relationship('MeetingModel', backref='host_zone', lazy=True)

    
    def __repr__(self):
        return f"<Zone {self.name}>"
    


    
class MeetingModel(db.Model):
     _tablename_ = 'meetings'
     id = db.Column(db.Integer, primary_key=True)
     block_id = db.Column(db.Integer, db.ForeignKey('blocks.id'), nullable=False)
     zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'), nullable=False)
     organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # the user who created the meeting
     date = db.Column(db.DateTime, nullable=False)

        
     def _repr_(self):
         return f"<Meeting {self.id} on {self.date}>"


class BankModel(db.Model):
    __tablename__ = 'banks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),nullable=False)
    paybill_no = db.Column(db.Integer,nullable=False)
    total_transactions = db.relationship('PaymentModel',backref='total_transactions',lazy=True)
    
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

    # Payment association with a specific block
    block_id = db.Column(db.Integer, db.ForeignKey('blocks.id'), nullable=False)
    
    # Payment association with a specific user (payer)
    payer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"<Payment {self.amount} by Member {self.payer_id}>"

    @classmethod
    def get_contributions_by_member(cls, user_id):
        """Get all contributions made by a specific member."""
        return cls.query.filter_by(payer_id=user_id).all()

    @classmethod
    def get_contributions_by_block(cls, block_id):
        """Get all contributions for a specific block."""
        return cls.query.filter_by(block_id=block_id).all()


class CommunicationModel(db.Model):
    __tablename__ = 'communications'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    member_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"<Message from Member {self.member_id}>"
    
# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, UserModel, Role)