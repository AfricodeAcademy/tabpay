from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore
from ..extensions import db
import uuid

# Association table for many-to-many relationship between Member and Block
member_blocks = db.Table('member_blocks',
    db.Column('member_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('block_id', db.Integer, db.ForeignKey('blocks.id'), primary_key=True)
)

# Association table for many-to-many relationship between User and Role
roles_users = db.Table('roles_users',
    db.Column('member_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)

class UmbrellaModel(db.Model):
    __tablename__ = 'umbrellas'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)

    # Relationship with block
    blocks = db.relationship('BlockModel', backref='parent_umbrella', lazy=True)

    def __repr__(self):
        return f"<Umbrella {self.name}>"

class BlockModel(db.Model):
    __tablename__ = 'blocks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_umbrella_id = db.Column(db.Integer, db.ForeignKey('umbrellas.id'), nullable=False)

    # Relationship with zone
    zones = db.relationship('ZoneModel', backref='parent_block', lazy=True)
    # Payments made to this block
    payments = db.relationship('PaymentModel', backref='block_payments', lazy=True)

    def __repr__(self):
        return f"<Block {self.name}>"

class ZoneModel(db.Model):
    __tablename__ = 'zones'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    parent_block_id = db.Column(db.Integer, db.ForeignKey("blocks.id"), nullable=False)

    # Relationship with members
    members = db.relationship('UserModel', backref='zone', lazy=True)

    def __repr__(self):
        return f"<Zone {self.name}>"

class UserModel(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True) 
    password = db.Column(db.String(255))
    full_name = db.Column(db.String(255))
    id_number = db.Column(db.Integer, index=True)  # Added index
    phone_number = db.Column(db.String(80), unique=True, index=True)  # Optimized with index
    active = db.Column(db.Boolean, default=True)
    registered_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    zone_id = db.Column(db.Integer,db.ForeignKey('zones.id'))

    # Relationships
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    messages = db.relationship('CommunicationModel', backref='author', lazy=True)
    payments = db.relationship('PaymentModel', backref='payer', lazy=True)
    
    # Many-to-many relationship with blocks
    block_memberships = db.relationship('BlockModel', secondary=member_blocks, backref=db.backref('users', lazy=True))

    def __repr__(self):
        return f"<Member {self.full_name}>"

class PaymentModel(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    mpesa_id = db.Column(db.String(255))  # Optimized for Mpesa ID length
    account_number = db.Column(db.String(80))
    source_phone_number = db.Column(db.String(80))
    amount = db.Column(db.Integer)
    payment_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    transaction_status = db.Column(db.Boolean, default=False)
    
    # Payment association with a specific block
    block_id = db.Column(db.Integer, db.ForeignKey('blocks.id'), nullable=False)
    
    # Payment association with a specific user (payer)
    payer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"<Payment {self.amount} by Member {self.payer_id}>"

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
