from sqlalchemy.exc import SQLAlchemyError
from flask import Blueprint
from werkzeug.exceptions import HTTPException
from flask_restful import Api,Resource, marshal_with, abort, fields, reqparse
from ..utils import db
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore
from flask_security.utils import hash_password
import uuid


api_bp = Blueprint('api', __name__)
api = Api(api_bp)

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
    email = db.Column(db.String(255), unique=True, nullable=True)  # Email may be null for non-login members
    password = db.Column(db.String(255), nullable=True)  # Auto-generated password can be nullable
    full_name = db.Column(db.String(255))
    id_number = db.Column(db.Integer, index=True,unique=True)  
    phone_number = db.Column(db.String(80), unique=True, index=True)
    active = db.Column(db.Boolean, default=True)
    bank = db.Column(db.String(50))
    acc_number = db.Column(db.String(50))
    registered_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    zone = db.Column(db.String(100))
    confirmed_at = db.Column(db.DateTime)
    webauth = db.relationship('WebAuth', backref='user', uselist=False)


    # Relationships
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    messages = db.relationship('CommunicationModel', backref='author', lazy=True)
    payments = db.relationship('PaymentModel', backref='payer', lazy=True)
    
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
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))  
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
    

   
class ZoneModel(db.Model):
    __tablename__ = 'zones'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    parent_block_id = db.Column(db.Integer, db.ForeignKey("blocks.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    
    def __repr__(self):
        return f"<Zone {self.name}>"

class PaymentModel(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    mpesa_id = db.Column(db.String(255), nullable=False)  
    account_number = db.Column(db.String(80), nullable=False)
    source_phone_number = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    payment_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    transaction_status = db.Column(db.Boolean, default=False)

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


# Argument parsers for different resources
umbrella_args = reqparse.RequestParser()
umbrella_args.add_argument('name', type=str, required=True, help='Umbrella Name is required')
umbrella_args.add_argument('location', type=str, required=True, help='Umbrella location is required')

block_args = reqparse.RequestParser()
block_args.add_argument('name', type=str, required=True, help='Block Name is required')
block_args.add_argument('parent_umbrella_id', type=int, required=True, help='Parent Umbrella is required')

zone_args = reqparse.RequestParser()
zone_args.add_argument('name', type=str, required=True, help='Zone Name is required')
zone_args.add_argument('parent_block_id', type=int, required=True, help='Parent Block is required')

user_args = reqparse.RequestParser()
user_args.add_argument('email', type=str, required=True, help='Email is required')
user_args.add_argument('password', type=str, required=True, help='Password is required')

communication_args = reqparse.RequestParser()
communication_args.add_argument('content', type=str, required=True, help='Content is required')
communication_args.add_argument('user_id', type=int, required=True, help='Author is required')

payment_args = reqparse.RequestParser()
payment_args.add_argument('payer_id', type=int, required=True, help='Payer is required')
payment_args.add_argument('source_phone_number', type=str, required=True, help='Source phone number is required')  # Changed to str
payment_args.add_argument('amount', type=float, required=True, help='Amount is required')

# Fields for serialization
user_fields = {
    "id": fields.Integer,
    "full_name": fields.String,
    "email": fields.String,
    "password": fields.String,
    "id_number": fields.Integer,
    "phone_number": fields.String,  # Changed to String
    "active": fields.Boolean,
    "zone_id": fields.Integer,
    "bank": fields.String,
    "acc_number": fields.String,  # Changed to String
    "registered_at": fields.DateTime,
    "updated_at": fields.DateTime,
    "message": fields.String(attribute="author.full_name")
}

communication_fields = {
    "id": fields.Integer,
    "content": fields.String,
    "user_id": fields.Integer,
    "created_at": fields.DateTime,
    "updated_at": fields.DateTime
}

payment_fields = {
    "id": fields.Integer,
    "payer_id": fields.Integer,
    "amount": fields.Float,
    "payment_date": fields.DateTime,
    "mpesa_id": fields.String,
    "account_number": fields.String,  # Changed to String
    "source_phone_number": fields.String,  # Changed to String
    "transaction_status": fields.Boolean
}

block_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "umbrella_id": fields.Integer
}

umbrella_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "location": fields.String
}

zone_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "parent_block_id": fields.Integer
}

class Users(Resource):
    @marshal_with(user_fields)
    def get(self):
        try:
            users = UserModel.query.all()
            return users, 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

    @marshal_with(user_fields)
    def post(self):
        try:
            args = user_args.parse_args()
            existing_user = UserModel.query.filter_by(email=args['email']).first()
            
            if existing_user:
                error_message = {"error": "User already exists"}
                abort(409, message=error_message)
            
            new_user = UserModel(**args)
            db.session.add(new_user)
            db.session.commit()
            return new_user, 201
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

class User(Resource):
    @marshal_with(user_fields)
    def get(self, id):
        try:
            user = UserModel.query.get_or_404(id)
            return user, 200
                   
        except SQLAlchemyError as e:
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()   

    @marshal_with(user_fields)
    def patch(self, id):
        try:
            args = user_args.parse_args()
            existing_user = UserModel.query.get_or_404(id)
            
            if existing_user:
                for key, value in args.items():
                    setattr(existing_user, key, value)
                db.session.commit()
                return existing_user, 200
            
            abort(404, message={"error": "User not found"})
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close() 

    @marshal_with(user_fields)
    def delete(self, id):
        try:
            existing_user = UserModel.query.get_or_404(id)
            
            if existing_user:
                db.session.delete(existing_user)
                db.session.commit()
                users = UserModel.query.all()
                return users, 200
            
            abort(404, message={"error": "User not found"})
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()




class Umbrellas(Resource):
    @marshal_with(umbrella_fields)
    def get(self):
        try:
            umbrellas = UmbrellaModel.query.all()
            return umbrellas, 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

    @marshal_with(umbrella_fields)
    def post(self):
        try:
            args = umbrella_args.parse_args()
            new_umbrella = UmbrellaModel(**args)
            db.session.add(new_umbrella)
            db.session.commit()
            return new_umbrella, 201
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

class Umbrella(Resource):
    @marshal_with(umbrella_fields)
    def get(self, id):
        try:
            umbrella = UmbrellaModel.query.get_or_404(id)
            return umbrella, 200
        
        except SQLAlchemyError as e:
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

    @marshal_with(umbrella_fields)
    def patch(self, id):
        try:
            args = umbrella_args.parse_args()
            umbrella = UmbrellaModel.query.get_or_404(id)
            
            for key, value in args.items():
                setattr(umbrella, key, value)
            db.session.commit()
            return umbrella, 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

    @marshal_with(umbrella_fields)
    def delete(self, id):
        try:
            umbrella = UmbrellaModel.query.get_or_404(id)
            db.session.delete(umbrella)
            db.session.commit()
            umbrellas = UmbrellaModel.query.all()
            return umbrellas, 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()







class Communications(Resource):
    @marshal_with(communication_fields)
    def get(self):
        try:
            communications = CommunicationModel.query.all()
            return communications, 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

    @marshal_with(communication_fields)
    def post(self):
        try:
            args = communication_args.parse_args()
            new_communication = CommunicationModel(**args)
            db.session.add(new_communication)
            db.session.commit()
            return new_communication, 201
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

class Communication(Resource):
    @marshal_with(communication_fields)
    def get(self, id):
        try:
            communication = CommunicationModel.query.get_or_404(id)
            return communication, 200
        
        except SQLAlchemyError as e:
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

    @marshal_with(communication_fields)
    def patch(self, id):
        try:
            args = communication_args.parse_args()
            communication = CommunicationModel.query.get_or_404(id)
            
            for key, value in args.items():
                setattr(communication, key, value)
            db.session.commit()
            return communication, 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

    @marshal_with(communication_fields)
    def delete(self, id):
        try:
            communication = CommunicationModel.query.get_or_404(id)
            db.session.delete(communication)
            db.session.commit()
            communications = CommunicationModel.query.all()
            return communications, 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()




class Payments(Resource):
    @marshal_with(payment_fields)
    def get(self):
        try:
            payments = PaymentModel.query.all()
            return payments, 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

    @marshal_with(payment_fields)
    def post(self):
        try:
            args = payment_args.parse_args()
            new_payment = PaymentModel(**args)
            db.session.add(new_payment)
            db.session.commit()
            return new_payment, 201
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

class Payment(Resource):
    @marshal_with(payment_fields)
    def get(self, id):
        try:
            payment = PaymentModel.query.get_or_404(id)
            return payment, 200
        
        except SQLAlchemyError as e:
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

    @marshal_with(payment_fields)
    def patch(self, id):
        try:
            args = payment_args.parse_args()
            payment = PaymentModel.query.get_or_404(id)
            
            for key, value in args.items():
                setattr(payment, key, value)
            db.session.commit()
            return payment, 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

    @marshal_with(payment_fields)
    def delete(self, id):
        try:
            payment = PaymentModel.query.get_or_404(id)
            db.session.delete(payment)
            db.session.commit()
            payments = PaymentModel.query.all()
            return payments, 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()





class Blocks(Resource):
    @marshal_with(block_fields)
    def get(self):
        try:
            blocks = BlockModel.query.all()
            return blocks, 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

    @marshal_with(block_fields)
    def post(self):
        try:
            args = block_args.parse_args()
            new_block = BlockModel(**args)
            db.session.add(new_block)
            db.session.commit()
            return new_block, 201
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

class Block(Resource):
    @marshal_with(block_fields)
    def get(self, id):
        try:
            block = BlockModel.query.get_or_404(id)
            return block, 200
        
        except SQLAlchemyError as e:
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

    @marshal_with(block_fields)
    def patch(self, id):
        try:
            args = block_args.parse_args()
            block = BlockModel.query.get_or_404(id)
            
            for key, value in args.items():
                setattr(block, key, value)
            db.session.commit()
            return block, 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

    @marshal_with(block_fields)
    def delete(self, id):
        try:
            block = BlockModel.query.get_or_404(id)
            db.session.delete(block)
            db.session.commit()
            blocks = BlockModel.query.all()
            return blocks, 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()





class Zones(Resource):
    @marshal_with(zone_fields)
    def get(self):
        try:
            zones = ZoneModel.query.all()
            return zones, 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

    @marshal_with(zone_fields)
    def post(self):
        try:
            args = zone_args.parse_args()
            new_zone = ZoneModel(**args)
            db.session.add(new_zone)
            db.session.commit()
            return new_zone, 201
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

class Zone(Resource):
    @marshal_with(zone_fields)
    def get(self, id):
        try:
            zone = ZoneModel.query.get_or_404(id)
            return zone, 200
        
        except SQLAlchemyError as e:
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

    @marshal_with(zone_fields)
    def patch(self, id):
        try:
            args = zone_args.parse_args()
            zone = ZoneModel.query.get_or_404(id)
            
            for key, value in args.items():
                setattr(zone, key, value)
            db.session.commit()
            return zone, 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()

    @marshal_with(zone_fields)
    def delete(self, id):
        try:
            zone = ZoneModel.query.get_or_404(id)
            db.session.delete(zone)
            db.session.commit()
            zones = ZoneModel.query.all()
            return zones, 200
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_message = {"error": "Database error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        except HTTPException as e:
            error_message = {"error": "HTTP error occurred", "details": str(e)}
            abort(e.code, message=error_message)
        
        except Exception as e:
            error_message = {"error": "Unexpected error occurred", "details": str(e)}
            abort(500, message=error_message)
        
        finally:
            db.session.close()


api.add_resource(Users, '/api/v1/users/')
api.add_resource(User, '/api/v1/users/<int:id>/')
api.add_resource(Communications, '/api/v1/communications/')
api.add_resource(Communication, '/api/v1/communications/<int:id>/')
api.add_resource(Payments, '/api/v1/payments/')
api.add_resource(Payment, '/api/v1/payments/<int:id>/')
api.add_resource(Blocks, '/api/v1/blocks/')
api.add_resource(Block, '/api/v1/blocks/<int:id>/')
api.add_resource(Umbrellas, '/api/v1/umbrellas/')
api.add_resource(Umbrella, '/api/v1/umbrellas/<int:id>/')
api.add_resource(Zones, '/api/v1/zones/')
api.add_resource(Zone, '/api/v1/zones/<int:id>/')
