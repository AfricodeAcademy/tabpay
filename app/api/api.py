from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException
from flask_restful import Resource, marshal_with, abort, fields, reqparse
from app.extensions import db
from app.models.models import UserModel, CommunicationModel, UmbrellaModel, PaymentModel, BlockModel, ZoneModel

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




    # # Register Route (API)
    # @app.route('/api/v1/register', methods=['POST'])
    # def api_register():
    #     email = request.json.get('email')
    #     password = request.json.get('password')
    #     hashed_password = generate_password_hash(password)
    #     user = UserModel.query.filter_by(email=email).first()
    #     if user:
    #         return jsonify({"message": "User already exists"}), 409
    #     new_user = UserModel(email=email, password=hashed_password)
    #     db.session.add(new_user)
    #     db.session.commit()
    #     return jsonify({"message": "User created"}), 201

    # # Login Route (API)
    # @app.route('/api/v1/login', methods=['POST'])
    # def api_login():
    #     email = request.json.get('email')
    #     password = request.json.get('password')
    #     user = UserModel.query.filter_by(email=email).first()
    #     if user and check_password_hash(user.password, password):
    #         login_user(user)
    #         return jsonify({"message": "Logged in"}), 200
    #     return jsonify({"message": "Invalid credentials"}), 401

    # # Logout Route (API)
    # @app.route('/api/v1/logout', methods=['POST'])
    # @login_required
    # def api_logout():
    #     logout_user()
    #     return jsonify({"message": "Logged out"}), 200