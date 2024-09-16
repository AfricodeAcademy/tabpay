from app.extensions import db

# Association table for many-to-many relationship between User and Block
user_block_association = db.Table('user_block_association',
     db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
     db.Column('block_id', db.Integer, db.ForeignKey('blocks.id'), primary_key=True)
 )


class UmbrellaModel(db.Model):
    __tablename__ = 'umbrellas'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
   
     # Relationship with block
    blocks = db.relationship('BlockModel', backref='umbrella', lazy=True)

    def __repr__(self):
        return f"<Umbrella {self.name}>"
    
   

class BlockModel(db.Model):
    __tablename__ = 'blocks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    parent_umbrella_id = db.Column(db.Integer, db.ForeignKey('umbrellas.id'), nullable=False)

    # Relationship with zone
    zones = db.relationship('ZoneModel', backref='block', lazy=True)

    
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



class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(80), nullable=False)
    id_number = db.Column(db.Integer, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.Integer, unique=True, nullable=False)
    village = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.String(255), nullable=False)
    is_active_member = db.Column(db.Boolean)
    registered_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    zone_id = db.Column(db.Integer, db.ForeignKey('zones.id'), nullable=False)
    
    
    # Payment and message relationships
    messages = db.relationship('CommunicationModel', backref='author', lazy=True)
    payments = db.relationship('PaymentModel', backref='payer', lazy=True)
   
    
    # Many-to-many relationship
    block_memberships = db.relationship('BlockModel', secondary=user_block_association, backref=db.backref('members', lazy=True))

    def __repr__(self):
        return f"<Member {self.full_name}>"



class CommunicationModel(db.Model):
    __tablename__ = 'communications'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime,default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
  
    def __repr__(self):
        return f"<Message from Member {self.user_id}>"

    

class PaymentModel(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    payment_date = db.Column(db.DateTime, default=db.func.current_timestamp(),nullable=False)
    bank = db.Column(db.String(80))
    acc_number = db.Column(db.Integer)
    payment_method = db.Column(db.String(20), nullable=False)
    status = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<Payment {self.amount} by Member {self.payer_id}>"
   




